import binascii
import hmac
from hashlib import sha256
import oauth2 as oauth


class SignatureMethod_HMAC_SHA256(oauth.SignatureMethod):
    name = 'HMAC-SHA256'

    def signing_base(self, request, consumer, token):
        if not hasattr(request, 'normalized_url') or request.normalized_url is None:
            raise ValueError("Base URL for request is not set.")

        sig = (
            oauth.escape(request.method),
            oauth.escape(request.normalized_url),
            oauth.escape(request.get_normalized_parameters()),
        )

        key = '%s&' % oauth.escape(consumer.secret)
        if token:
            key += oauth.escape(token.secret)
        raw = '&'.join(sig)
        return key.encode('ascii'), raw.encode('ascii')

    def sign(self, request, consumer, token):
        """Builds the base signature string."""
        key, raw = self.signing_base(request, consumer, token)

        hashed = hmac.new(key, raw, sha256)

        # Calculate the digest base 64.
        return binascii.b2a_base64(hashed.digest())[:-1]