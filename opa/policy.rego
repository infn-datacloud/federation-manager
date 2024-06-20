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

default is_site_admin := false
default is_site_tester := false
default is_user_group_mgr := false
default is_sla_mod := false
default is_admin := false

bearer_token := t if {
	# Bearer tokens are contained inside of the HTTP Authorization header. This rule
	# parses the header and extracts the Bearer token value. If no Bearer token is
	# provided, the `bearer_token` value is undefined.
	v := input.authorization
	startswith(v, "Bearer ")
	t := substring(v, count("Bearer "), -1)
}

claims := payload if {
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

# Generic rule:
# Set the attribute true if one of the user entitlements is within the
# attribute's accepted entitlements.

is_site_admin if {
	some role in claims.groups
	role in data.site_admin_entitlements
}

is_site_tester if {
	some role in claims.groups
	role in data.site_tester_entitlements
}

is_user_group_mgr if {
	some role in claims.groups
	role in data.user_group_mgr_entitlements
}

is_sla_mod if {
	some role in claims.groups
	role in data.sla_mod_entitlements
}

is_admin if  {
	some role in claims.groups
	role in data.admin_entitlemnts
}

user_roles := {
	"is_site_admin": is_site_admin,
	"is_site_tester": is_site_tester,
	"is_user_group_mgr": is_user_group_mgr,
	"is_sla_mod": is_sla_mod,
	"is_admin": is_admin
}
