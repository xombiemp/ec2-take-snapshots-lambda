from __future__ import print_function
from boto3 import resource
from botocore.exceptions import ClientError

# You must populate either the VOLUMES variable or the
# VOLUME_TAGS variable, but not both.

# List of volume-ids, or "all" for all volumes
# eg. ["vol-12345678", "vol-87654321"] or ["all"]
VOLUMES = []

# Dictionary of tags to use to filter the volumes. May specify multiple
# eg. {'key': 'value'} or {'key1': 'value1', 'key2': 'value2', ...}
VOLUME_TAGS = {}

# Dictionary of tags to apply to the created snapshots.
# eg. {'key': 'value'} or {'key1': 'value1', 'key2': 'value2', ...}
SNAPSHOT_TAGS = {}

# AWS region in which the volumes exist
REGION = "us-east-1"


def take_snapshots(volume, tags_kwargs):
    if NOOP is False:
        snapshot = volume.create_snapshot(
                   Description='Created with ec2-take-snapshots'
                   )
        if tags_kwargs:
            snapshot.create_tags(**tags_kwargs)
    else:
        snapshot = None
    print("Snapshot {} created{} for volume {}".format(
          snapshot.snapshot_id if snapshot else "snapshot_id",
          NOT_REALLY_STR, volume.volume_id)
          )


def process_tags():
    tags = []
    tags_kwargs = {}
    # AWS allows 10 tags per resource
    if SNAPSHOT_TAGS and len(SNAPSHOT_TAGS) <= 10:
        for key, value in SNAPSHOT_TAGS.iteritems():
            tags.append({'Key': key, 'Value': value})
        tags_kwargs['Tags'] = tags
    return tags_kwargs


def get_tag_volumes(ec2):
    collection_filter = []
    for key, value in VOLUME_TAGS.iteritems():
        collection_filter.append(
            {
                "Name": "tag:" + key,
                "Values": [value]
            }
        )
    tag_volumes = ec2.volumes.filter(Filters=collection_filter)
    iterator = (i for i in tag_volumes)
    count = sum(1 for _ in iterator)
    tag_volumes.count = count
    return tag_volumes


def print_summary(counts):
    print("\nSUMMARY:\n")
    print("Snapshots created:  {}{}".format(counts,
          NOT_REALLY_STR if counts > 0 else ""))
    print("-------------------------------------------\n")


def main(event, context):
    global NOOP
    global NOT_REALLY_STR

    NOOP = event['noop'] if 'noop' in event else False
    NOT_REALLY_STR = " (not really)" if NOOP is not False else ""
    ec2 = resource("ec2", region_name=REGION)
    tags_kwargs = process_tags()
    snap_count = 0

    if VOLUMES and not VOLUME_TAGS:
        if len(VOLUMES) == VOLUMES.count("all"):
            all_volumes = ec2.volumes.all()
            for volume in all_volumes:
                take_snapshots(volume, tags_kwargs)
                snap_count += 1
        else:
            for volume_id in VOLUMES:
                volume = ec2.Volume(volume_id)
                try:
                    volume.describe_status()
                except ClientError:
                    print("No volumes found with the ID {}".format(volume_id))
                else:
                    take_snapshots(volume, tags_kwargs)
                    snap_count += 1
        print_summary(snap_count)
    elif VOLUME_TAGS and not VOLUMES:
        tag_volumes = get_tag_volumes(ec2)
        if tag_volumes.count > 0:
            for tag_volume in tag_volumes:
                take_snapshots(tag_volume, tags_kwargs)
                snap_count += 1
        else:
            print("No volumes found with the given tags.")
        print_summary(snap_count)
    else:
        print("You must populate either the VOLUMES OR"
              " the VOLUME_TAGS variable."
              )
