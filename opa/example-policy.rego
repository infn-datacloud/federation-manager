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
package fed_mgr

import rego.v1

default claim := ""

claim := issuer.claim if {
	some issuer in data.trusted_issuers
	issuer.endpoint == input.user_info.iss
}

default is_user := false

is_user if {
	some issuer in data.trusted_issuers
	issuer.endpoint == input.user_info.iss
}

default is_admin := false

is_admin if {
	is_user
	some role in input.user_info[claim]
	role in data.admin_entitlements
}

default allow := false

# Allow if user is admin
allow if {
	is_admin
}

# Allow users on permitted endpoints
allow if {
	is_user
	some endpoint in data.user_endpoints
	endpoint.method == input.method
	endpoint.path == input.path
}
