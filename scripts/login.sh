#!/bin/bash

set -e

OIDC_PROVIDER="${OIDC_PROVIDER}"
OIDC_CLIENT_ID="${OIDC_CLIENT_ID}"
OIDC_CLIENT_SECRET="${OIDC_CLIENT_SECRET}"
OIDC_SCOPE="openid profile email"
OIDC_GRANT_TYPE="urn:ietf:params:oauth:grant-type:device_code"

well_known="${OIDC_PROVIDER}/.well-known/openid-configuration"
response=$(mktemp)

curl -sS "${well_known}" -o "${response}"

device_authorization_endpoint=$(jq -r '.device_authorization_endpoint' "${response}")
token_endpoint=$(jq -r '.token_endpoint' "${response}")

authorization=$(echo -en "${OIDC_CLIENT_ID}:${OIDC_CLIENT_SECRET}" | base64 -w0)

# Request Device Code
curl -sS -X POST "${device_authorization_endpoint}" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -H "Authorization: Basic ${authorization}" \
    -d "client_id=${OIDC_CLIENT_ID}" \
    -d "scope=${OIDC_SCOPE}" \
    -d "client_secret=${OIDC_CLIENT_SECRET}" \
    -o "${response}"

# Parse response
device_code=$(jq -r '.device_code' "${response}")
user_code=$(jq -r '.user_code' "${response}")
verification_uri=$(jq -r '.verification_uri' "${response}")
interval=$(jq -r '.interval' "${response}" | sed s/null/5/g) # defaults to 5 seconds

# Prompt user for authorization
echo "Please go to ${verification_uri} and enter the user code: ${user_code}" >&2
while true; do
    sleep "${interval}"
    curl -sS -X POST "${token_endpoint}" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -H "Authorization: Basic ${authorization}" \
        -d "client_id=${OIDC_CLIENT_ID}" \
        -d "device_code=${device_code}" \
        -d "grant_type=${OIDC_GRANT_TYPE}" \
        -o "${response}"

    # Check if the response is empty
    if [[ -z ${response} ]]; then
        continue
    fi

    # Check for errors

    error=$(jq -r '.error' "${response}")
    if [[ "${error}" == "authorization_pending" ]]; then
        continue
    elif [[ -n ${error} && ${error} != "null" ]]; then
        echo "An error occurred: ${error}"
        exit 1
    fi

    access_token=$(jq -r '.access_token' "${response}")
    refresh_token=$(jq -r '.refresh_token' "${response}")
    break
done

echo $access_token

rm "${response}"
