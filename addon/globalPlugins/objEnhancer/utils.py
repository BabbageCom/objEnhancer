import screenBitmap
import hashlib
import base64


def locationBitmapHash(location):
	sb = screenBitmap.ScreenBitmap(location.width, location.height)
	pixels = sb.captureImage(*location)
	digest = hashlib.sha1(bytearray(pixels)).digest()
	return base64.b64encode(digest).decode("ascii")


def bitmapHash(obj, padding=10):
	location = obj.location.expandOrShrink(-1 * padding)
	return locationBitmapHash(location)
