from boto3 import resource

# You must populate either the VOLUMES variable or the
# VOLUME_TAGS variable, but not both.

# List of volume-ids
# eg. ["vol-12345678"] or ["vol-12345678", "vol-87654321", ...]
VOLUMES = []

# Dictionary of tags to use to filter the volumes. May specify multiple
# eg. {"key": "value"} or {"key1": "value1", "key2": "value2", ...}
VOLUME_TAGS = {}

# Dictionary of tags to apply to the created snapshots
# eg. {"key": "value"} or {"key1": "value1", "key2": "value2", ...}
SNAPSHOT_TAGS = {}

# AWS regions in which the volumes exist
# eg. ["us-east-1"] or ["us-east-1", "us-west-1", ...]
REGIONS = ["us-east-1"]


def take_snapshots(volume, region, tags_kwargs):
    if NOOP is False:
        snapshot = volume.create_snapshot(
                   Description="Created with ec2-take-snapshots"
                   )
        if tags_kwargs:
            snapshot.create_tags(**tags_kwargs)
    else:
        snapshot = None
    print("Snapshot {} created{} for volume {} in {}".format(
          snapshot.snapshot_id if snapshot else "snapshot_id",
          NOT_REALLY_STR, volume.volume_id, region)
          )


def process_tags(volume):
    tags = []
    tags_kwargs = {}
    if "Name" not in SNAPSHOT_TAGS.keys():
        for tag in volume.tags:
            if tag["Key"] == "Name":
                SNAPSHOT_TAGS["Name"] = tag["Value"]
                break
    if SNAPSHOT_TAGS:
        if len(SNAPSHOT_TAGS) <= 10:
            for key, value in SNAPSHOT_TAGS.items():
                tags.append({"Key": key, "Value": value})
            tags_kwargs["Tags"] = tags
        else:
            print("AWS only allows for 10 or less tags per snapshot.")
    return tags_kwargs


def get_tag_volumes(ec2):
    collection_filter = []
    for key, value in VOLUME_TAGS.items():
        collection_filter.append(
            {
                "Name": "tag:" + key,
                "Values": [value]
            }
        )
    collection = ec2.volumes.filter(Filters=collection_filter)
    return list(collection)


def print_summary(counts, region):
    print("\nSUMMARY:\n")
    print("Snapshots created in {}:  {}{}".format(region, counts,
          NOT_REALLY_STR if counts > 0 else ""))
    print("-------------------------------------------\n")


def main(event, context):
    global NOOP
    global NOT_REALLY_STR

    NOOP = event["noop"] if "noop" in event else False
    NOT_REALLY_STR = " (not really)" if NOOP is not False else ""
    for region in REGIONS:
        ec2 = resource("ec2", region_name=region)
        snap_count = 0

        if VOLUMES and not VOLUME_TAGS:
            for volume_id in VOLUMES:
                volume = ec2.Volume(volume_id)
                try:
                    volume.load()
                except:
                    print("No volumes found with the ID {} in {}".format(
                          volume_id, region)
                          )
                else:
                    tags_kwargs = process_tags(volume)
                    take_snapshots(volume, region, tags_kwargs)
                    snap_count += 1
            print_summary(snap_count, region)
        elif VOLUME_TAGS and not VOLUMES:
            tag_string = " ".join("{}={}".format(key, val) for (key, val) in
                                  VOLUME_TAGS.items()
                                  )
            volumes = get_tag_volumes(ec2)
            if volumes:
                for volume in volumes:
                    tags_kwargs = process_tags(volume)
                    take_snapshots(volume, region, tags_kwargs)
                    snap_count += 1
            else:
                print("No volumes found with tags: {} in {}.".format(
                      tag_string, region)
                      )
            print_summary(snap_count, region)
        else:
            print("You must populate either the VOLUMES OR"
                  " the VOLUME_TAGS variable."
                  )
