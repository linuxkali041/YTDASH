"""
OAuth 2.0 authentication flow for Google/YouTube.
Handles authorization, token exchange, and cookie extraction.
"""

from typing import Dict, Optional, Tuple
from authlib.integrations.starlette_client import OAuth
from starlette.requests import Request
import httpx
from utils.errors import AuthenticationError, ConfigurationError
from utils.logging_config import get_logger

logger = get_logger(__name__)


class OAuthManager:
    """Manages Google OAuth 2.0 flow."""
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        scopes: list
    ):
        """
        Initialize OAuth manager.
        
        Args:
            client_id: Google OAuth client ID
            client_secret: Google OAuth client secret
            redirect_uri: OAuth redirect URI
            scopes: List of OAuth scopes to request
            
        Raises:
            ConfigurationError: If OAuth credentials are missing
        """
        if not client_id or not client_secret:
            raise ConfigurationError("OAuth credentials not configured")
        
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scopes = scopes
        
        # Initialize OAuth client
        self.oauth = OAuth()
        self.oauth.register(
            name='google',
            client_id=client_id,
            client_secret=client_secret,
            server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
            client_kwargs={'scope': ' '.join(scopes)}
        )
        
        logger.info("OAuth manager initialized")
    
    async def get_authorization_url(self, state: str) -> str:
        """
        Generate OAuth authorization URL.
        
        Args:
            state: CSRF protection state parameter
            
        Returns:
            Authorization URL
        """
        try:
            # Build authorization URL
            auth_url = (
                f"https://accounts.google.com/o/oauth2/v2/auth?"
                f"client_id={self.client_id}&"
                f"redirect_uri={self.redirect_uri}&"
                f"response_type=code&"
                f"scope={' '.join(self.scopes)}&"
                f"state={state}&"
                f"access_type=offline&"
                f"prompt=consent"
            )
            
            logger.debug(f"Generated authorization URL with state {state}")
            return auth_url
        except Exception as e:
            logger.error(f"Failed to generate authorization URL: {e}")
            raise AuthenticationError(f"Failed to generate authorization URL: {e}")
    
    async def exchange_code_for_token(self, code: str) -> Dict:
        """
        Exchange authorization code for access token.
        
        Args:
            code: Authorization code from callback
            
        Returns:
            Token response containing access_token, refresh_token, etc.
            
        Raises:
            AuthenticationError: If token exchange fails
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    'https://oauth2.googleapis.com/token',
                    data={
                        'code': code,
                        'client_id': self.client_id,
                        'client_secret': self.client_secret,
                        'redirect_uri': self.redirect_uri,
                        'grant_type': 'authorization_code'
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"Token exchange failed: {response.text}")
                    raise AuthenticationError("Token exchange failed")
                
                token_data = response.json()
                logger.info("Successfully exchanged code for token")
                return token_data
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during token exchange: {e}")
            raise AuthenticationError(f"Token exchange failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during token exchange: {e}")
            raise AuthenticationError(f"Token exchange failed: {e}")
    
    async def get_user_info(self, access_token: str) -> Dict:
        """
        Get user information from Google.
        
        Args:
            access_token: OAuth access token
            
        Returns:
            User information (id, email, name, etc.)
            
        Raises:
            AuthenticationError: If user info request fails
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    'https://www.googleapis.com/oauth2/v2/userinfo',
                    headers={'Authorization': f'Bearer {access_token}'}
                )
                
                if response.status_code != 200:
                    logger.error(f"User info request failed: {response.text}")
                    raise AuthenticationError("Failed to get user info")
                
                user_info = response.json()
                logger.info(f"Retrieved user info for {user_info.get('email')}")
                return user_info
        except httpx.HTTPError as e:
            logger.error(f"HTTP error getting user info: {e}")
            raise AuthenticationError(f"Failed to get user info: {e}")
        except Exception as e:
            logger.error(f"Unexpected error getting user info: {e}")
            raise AuthenticationError(f"Failed to get user info: {e}")
    
    async def refresh_access_token(self, refresh_token: str) -> Dict:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_token: OAuth refresh token
            
        Returns:
            New token data
            
        Raises:
            AuthenticationError: If token refresh fails
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    'https://oauth2.googleapis.com/token',
                    data={
                        'refresh_token': refresh_token,
                        'client_id': self.client_id,
                        'client_secret': self.client_secret,
                        'grant_type': 'refresh_token'
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"Token refresh failed: {response.text}")
                    raise AuthenticationError("Token refresh failed")
                
                token_data = response.json()
                logger.info("Successfully refreshed access token")
                return token_data
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during token refresh: {e}")
            raise AuthenticationError(f"Token refresh failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during token refresh: {e}")
            raise AuthenticationError(f"Token refresh failed: {e}")
    
    async def extract_youtube_cookies(self, access_token: str) -> Dict[str, str]:
        """
        Extract YouTube session cookies using access token.
        
        Note: This is a simplified implementation. In practice, you may need to:
        1. Make an authenticated request to YouTube
        2. Extract cookies from the response
        3. Store relevant cookies (SAPISID, HSID, SSID, etc.)
        
        Args:
            access_token: OAuth access token
            
        Returns:
            Dictionary of YouTube cookies
        """
        try:
            # Make authenticated request to YouTube to establish session
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    'https://www.youtube.com',
                    headers={'Authorization': f'Bearer {access_token}'},
                    follow_redirects=True
                )
                
                # Extract cookies from response
                cookies = {}
                for cookie_name in ['SAPISID', 'HSID', 'SSID', 'SID', 'APISID', 'LOGIN_INFO']:
                    if cookie_name in response.cookies:
                        cookies[cookie_name] = response.cookies[cookie_name]
                
                if cookies:
                    logger.info(f"Extracted {len(cookies)} YouTube cookies")
                else:
                    logger.warning("No YouTube cookies found in response")
                
                return cookies
        except Exception as e:
            logger.error(f"Failed to extract YouTube cookies: {e}")
            # Return empty dict instead of failing - app can work without cookies
            return {}
