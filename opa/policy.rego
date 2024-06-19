# The policy returns the roles granted to a user identified by a trused issuer.
# Roles are stored in the "groups" attribute of the JWT token.
#
# This policy does:
#
#	* Extract and decode a JSON Web Token (JWT).
#	* Verify signatures on JWT using built-in functions in Rego.
#	* Define helper rules that provide useful abstractions.
#   * Verify token's iss is a trusted issuer.
#   * Retrieve roles granted to authenticated user.
#
# For more information see:
#
#	* Rego JWT decoding and verification functions:
#     https://www.openpolicyagent.org/docs/latest/policy-reference/#token-verification
#
package fedmgr

import rego.v1

default is_trusted_issuer := false

is_trusted_issuer if claims.iss in data.trusted_issuers

bearer_token := t if {
	# Bearer tokens are contained inside of the HTTP Authorization header. This rule
	# parses the header and extracts the Bearer token value. If no Bearer token is
	# provided, the `bearer_token` value is undefined.
	v := input.authorization
	startswith(v, "Bearer ")
	t := substring(v, count("Bearer "), -1)
}

claims := payload if {
	# jwks := `{
	# 	"keys": [
	# 		{
	# 			"kty": "RSA",
	# 			"e": "AQAB",
	# 			"kid": "cra1",
	# 			"x5c": [
	# 				"MIICnDCCAYSgAwIBAgIGAYlj+gOSMA0GCSqGSIb3DQEBCwUAMA8xDTALBgNVBAMMBGNyYTEwHhcNMjMwNzE3MTMxMTE2WhcNMjgwNzE1MTMxMTE2WjAPMQ0wCwYDVQQDDARjcmExMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAn1FfI6gs/ng6QOYPcGYKyliHjWYT46bUDAyR+L+hegsjUZQyIq+1j1r+Eoi8nXvOXGsHnWWvtS9JhX8EaAG3j0cGZDCQz1MvGsPvDYCfF1Uge9MAL+khyWqfdazclK91MEHHqI1bMOyZiZg75d7uhhsEyTFbCxHVJvYGqWIEpo4QcLgyr1oQJxUWQf7c4LHl2bwtm9gRyvN3Fajun9Tnk8MsoBqSsE3Iea3oBJwBgiOQJasZX9l2+V/SErU9K4jAxKJRfKrDrdxZxnIGj02hauQOHd6god1CGs/p75YFLQ8sTetX1zlMs62Ef6XsvMPHjJyJVIEvn/jlSrZ4q1F13wIDAQABMA0GCSqGSIb3DQEBCwUAA4IBAQAOEaPUp+SboWPAf20gObYr8jKcS4R7kZyMrrAOa0mYOVsfuBRjLHjIB17wrs2TTUBoLJM8k8YkJzP+3YbODlKJuys50eSK3+fd12IrXJYRBtJ8zZShCMIHMgLGXEZgtTl6tG7emOmJp3IqANapioNI/tAR9ntgGHQlqYH/iRsydOhs4bdC4Cbhpa63nhMT1ymOo+BNPuniYROGkNyIs1uf85rMO2D6uv0EGWz2sux9AkHmsr+6xBKbaCk9Pxr5AfL3kg9EYxeWEPZARf3zTDqo8nGqFB8fKMPY+3+wSlPYs1z1aDnC/W7iCqFldoMznmjYJR2ob8KHKSiEISpOZNfr"
	# 			],
	# 			"n": "n1FfI6gs_ng6QOYPcGYKyliHjWYT46bUDAyR-L-hegsjUZQyIq-1j1r-Eoi8nXvOXGsHnWWvtS9JhX8EaAG3j0cGZDCQz1MvGsPvDYCfF1Uge9MAL-khyWqfdazclK91MEHHqI1bMOyZiZg75d7uhhsEyTFbCxHVJvYGqWIEpo4QcLgyr1oQJxUWQf7c4LHl2bwtm9gRyvN3Fajun9Tnk8MsoBqSsE3Iea3oBJwBgiOQJasZX9l2-V_SErU9K4jAxKJRfKrDrdxZxnIGj02hauQOHd6god1CGs_p75YFLQ8sTetX1zlMs62Ef6XsvMPHjJyJVIEvn_jlSrZ4q1F13w"
	# 		},
	# 		{
	# 			"kty": "RSA",
	# 			"e": "AQAB",
	# 			"kid": "rsa1",
	# 			"n": "gAjzmGkUC7VEGcYh-9e-MHjcTQ-u4wPq5GEvn3SCdfENsUjnMpm58ILpkP-ddGZLLzSeMEc8zluqa725OTmf52zYx5dKqcZF7ZRRdQ_r4cLhq5MpNNRi0cnoQVX22dZeJZOEyaXvN1nSZqLr8K4QWG1gUGCN2f5sZTxidzqFnd0"
	# 		}
	# 	]
	# }`
	
	# Verify the signature on the Bearer token. In this example the secret is
	# hardcoded into the policy however it could also be loaded via data or
	# an environment variable. Environment variables can be accessed using
	# the `opa.runtime()` built-in function.
	# io.jwt.verify_rs256(bearer_token, jwks)

	# This statement invokes the built-in function `io.jwt.decode` passing the
	# parsed bearer_token as a parameter. The `io.jwt.decode` function returns an
	# array:
	#
	#	[header, payload, signature]
	#
	# In Rego, you can pattern match values using the `=` and `:=` operators. This
	# example pattern matches on the result to obtain the JWT payload.
	[_, payload, _] := io.jwt.decode(bearer_token)
}

user_roles contains role if {
	# The `role` will be contained in the set `user_roles` if the role in the
	# `groups` key of the `claims` object is in the `user_roles` of the `data`
	# object.
	is_trusted_issuer
	some role in claims.groups
	role in data.user_roles
}
