# tap-auth0

This is a fork of Jean-Nicholas Hould's [Singer](https://singer.io) tap that produces JSON-formatted data following the [Singer spec](https://github.com/singer-io/getting-started/blob/master/SPEC.md).

The original tap accesses the User endpoint of the Auth0 Management API. This fork initiates a User Export job, which allows for the retrieval of more than 1,000 users.

This tap:
- Pulls raw data from Auth0's [Management API v2](https://auth0.com/docs/api/management/v2)
- Extracts the following resources from Auth0
  - [Users](https://auth0.com/docs/api/management/v2#!/Users/get_users)

## Installation

```bash
> pip install https://github.com/hkuffel/tap-auth0.git
```

## Configuration

This tap requires a `config.json` which specifies details regarding [M2M](https://auth0.com/docs/dashboard/guides/applications/register-app-m2m) authentication. See [config.sample.json](config.sample.json) for an example.

To run `tap-auth0` with the configuration file, use this command:
a
```bash
› tap-auth0 -c my-config.json
```
