import gzip
import json
import os
from math import ceil
import shutil
import time
import urllib

from auth0.v3.authentication import GetToken
from auth0.v3.management import Auth0
import singer

CONFIG = {
    "domain": None,
    "non_interactive_client_id": None,
    "non_interactive_client_secret": None
}


def get_auth0_client():
    get_token = GetToken(CONFIG['domain'])
    token = get_token.client_credentials(
        CONFIG['non_interactive_client_id'],
        CONFIG['non_interactive_client_secret'],
        'https://{}/api/v2/'.format(CONFIG['domain'])
    )
    mgmt_api_token = token['access_token']
    return Auth0(CONFIG['domain'], mgmt_api_token)


def get_abs_path(path):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), path)


def load_schema(entity_name):
    schema = singer.utils.load_json(
        get_abs_path('schemas/{}.json'.format(entity_name))
    )
    return schema


def get_connections(auth_client):
    return auth_client.connections.all()


def start_user_export(auth_client, connection_id):
    return auth_client.jobs.export_users(
        body={
            'connection_id': connection_id,
            'format': 'json',
            'fields': [
                {'name': 'email'},
                {'name': 'email_verified'},
                {'name': 'user_id'},
                {'name': 'created_at'},
                {'name': 'updated_at'},
                {'name': 'last_login'},
                {'name': 'logins_count'},
                {'name': 'last_ip'},
                {
                    'name': 'app_metadata.has_pcd_subscription',
                    'export_as': 'has_pcd_subscription'
                },
                {'name': 'app_metadata.pcd_account_number', 'export_as': 'pcd_account_number'},
                {'name': 'app_metadata.pcd_status', 'export_as': 'pcd_status'},
                {'name': 'app_metadata.pcd_account_type', 'export_as': 'pcd_account_type'},
                {
                    'name': 'app_metadata.stripe[0].customer_id',
                    'export_as': 'stripe_customer_id'
                },
                {'name': 'app_metadata.coral_id', 'export_as': 'coral_id'},
                {'name': 'app_metadata.pcd_email', 'export_as': 'pcd_email'},
                {'name': 'app_metadata.pcd_geo', 'export_as': 'pcd_geo'},
                {'name': 'app_metadata.has_subscription', 'export_as': 'has_subscription'},
                {
                    'name': 'app_metadata.has_apple_subscription',
                    'export_as': 'has_apple_subscription'
                },
                {
                    'name': 'app_metadata.has_staff_subscription',
                    'export_as': 'has_staff_subscription'
                },
                {'name': 'identities[0].connection', 'export_as': 'provider'}
            ]
        }
    )


def get_job_status(auth_client, job_id):
    return auth_client.jobs.get(job_id)


def process_job_results(job_results_str):
    with open('raw_encoded_results.json', 'wb') as fp:
        fp.write(job_results_str)
    with gzip.open('raw_encoded_results.json', 'rb') as f_in:
        with open('decoded_results.json', 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    with open('decoded_results.json', 'r') as f:
        users = json.loads(
            '[' + f.read().replace('\n', ',')[:-1] + ']'
        )
    os.remove('raw_encoded_results.json')
    os.remove('decoded_results.json')
    return users


def list_all_users(auth_client, conn_id):
    users_schema = load_schema('users')
    singer.write_schema('users', users_schema, 'user_id')

    job_obj = start_user_export(auth_client, conn_id)
    job_id = job_obj['id']
    job_result_location = None
    while not job_result_location:
        job_status_obj = get_job_status(auth_client, job_id)
        if job_status_obj['status'] == 'completed':
            job_result_location = job_status_obj['location']
        else:
            time.sleep(7)
    job_results_str = urllib.request.urlopen(job_result_location).read()
    users = process_job_results(job_results_str)
    singer.write_records('users', users)


def main_impl():
    args = singer.utils.parse_args([
        "domain",
        "non_interactive_client_id",
        "non_interactive_client_secret"])

    CONFIG.update(args.config)
    auth_client = get_auth0_client()

    connection_ids = [cn['id'] for cn in get_connections(auth_client)]
    if len(connection_ids) > 0:
        for cn_id in connection_ids:
            list_all_users(auth_client, cn_id)
    else:
        list_all_users(auth_client, connection_ids[0])


def main():
    try:
        main_impl()
    except Exception as exc:
        raise exc


if __name__ == '__main__':
    main()
