#!/usr/bin/env python
"""
This program is to collect some AWS stuff 
"""
import boto3
import threading

from local_helpers.config import accounts_db
from local_helpers import assume_role, get_session, misc 
from local_helpers import elb_helper

if __name__ == "__main__":
    """main"""

    """bucket to hold results"""
    output_bucket = []

    """out of accounts_db, get list of available regions from first account"""
    regions = get_session.regions()

    if regions:
        """generate output header"""
        output_bucket.append(elb_helper.sg_rule_sets_by_elb_header())

        """go through each account and traverse each region"""
        """------------------------------------------------"""
        multi_thread = []

        """get tuple: account -> dict:, temp role creds -> dict:"""
        for account in accounts_db.accounts:
            """get temp creds from trusting roles"""
            role = assume_role.new_role(account)

            if role:
                for region in regions.get('Regions'):

                    """make an elb type client connection"""
                    elb = get_session.connect(
                    role, 
                    'elb', 
                    region_name=region.get('RegionName'))

                    """make an ec2 type client connection"""
                    ec2 = get_session.connect(
                    role, 
                    'ec2', 
                    region_name=region.get('RegionName'))

                    """
                    call elb.describe_load_balancers() in multithreading mode 
                    for better performance. otherwise performance sucks.
                    """
                    thread_call = threading.Thread(
                         target=elb_helper.sg_rule_sets_by_elb, 
                         args=(elb, ec2, account, region, output_bucket))
                    multi_thread.append(thread_call)
                    thread_call.start()

        """wait for all threads to finish"""
        for t in multi_thread:
            t.join()

        """output or export results"""
        if output_bucket:
            misc.output_lines(output_bucket)



