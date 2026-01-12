try:
    from download.models import *
    print("Models imported successfully")
    
    # Try instantiating some
    v = VideoInfoRequest(url="http://youtube.com/watch?v=123")
    print(v)
except Exception as e:
    import traceback
    traceback.print_exc()
