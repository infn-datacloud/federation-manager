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
	# Verify the signature on the Bearer token. In this example the secret is
	# hardcoded into the policy however it could also be loaded via data or
	# an environment variable. Environment variables can be accessed using
	# the `opa.runtime()` built-in function.
	# io.jwt.verify_hs256(bearer_token, "B41BD5F462719C6D6118E673A2389")

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
