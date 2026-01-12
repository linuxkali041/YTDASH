# How to Update Social Media Links

The social media buttons in the footer are currently set to placeholder links (`#facebook`, `#telegram`, etc.).

## To Update Your Social Media Links:

1. **Open the following files** in your code editor:
   - `static/index.html`
   - `static/login.html`
   - `static/register.html`
   - `static/admin/index.html` (if you added it there)

2. **Find and replace** the placeholder links with your actual social media URLs:

### Current Placeholder Code:
```html
<a href="#facebook" class="social-btn facebook">
<a href="#telegram" class="social-btn telegram">
<a href="#twitter" class="social-btn twitter">
<a href="#youtube" class="social-btn youtube">
```

### Replace With Your Links:
```html
<a href="https://facebook.com/your-profile" class="social-btn facebook" target="_blank" rel="noopener noreferrer">
<a href="https://t.me/your-channel" class="social-btn telegram" target="_blank" rel="noopener noreferrer">
<a href="https://twitter.com/your-handle" class="social-btn twitter" target="_blank" rel="noopener noreferrer">
<a href="https://youtube.com/@your-channel" class="social-btn youtube" target="_blank" rel="noopener noreferrer">
```

## Example:

**Before:**
```html
<a href="#facebook" class="social-btn facebook" aria-label="Visit Facebook page">
```

**After:**
```html
<a href="https://facebook.com/ahmed.hassan" class="social-btn facebook" target="_blank" rel="noopener noreferrer" aria-label="Visit Facebook page">
```

## Notes:

- `target="_blank"` - Opens link in new tab
- `rel="noopener noreferrer"` - Security best practice for external links
- Keep the existing classes and icons unchanged
- Only replace the `href="#..."` part

## Quick Find & Replace:

Use your editor's find and replace feature:

1. **Find:** `href="#facebook"`
   **Replace with:** `href="YOUR_FACEBOOK_URL" target="_blank" rel="noopener noreferrer"`

2. **Find:** `href="#telegram"`
   **Replace with:** `href="YOUR_TELEGRAM_URL" target="_blank" rel="noopener noreferrer"`

3. **Find:** `href="#twitter"`
   **Replace with:** `href="YOUR_TWITTER_URL" target="_blank" rel="noopener noreferrer"`

4. **Find:** `href="#youtube"`
   **Replace with:** `href="YOUR_YOUTUBE_URL" target="_blank" rel="noopener noreferrer"`

---

**Created by AhMed HaSsan**
