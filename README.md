# ec2-take-snapshots-lambda
An AWS Lambda function that takes EC2 snapshots

## Usage
This python script is a meant to be run as a scheduled AWS Lamdba function. This will take a snapshot of all the volumes you specify or every volume that matches a set of tags. This will automatically add a Name tag to the snapshots with the corresponding volume Name tag if it exists. You can use this script in conjuction with https://github.com/xombiemp/ec2-purge-snapshots-lambda to create a rolling backup retention plan. You will need to configure the following variables at the top of the script:  
You must populate either the VOLUMES variable or the VOLUME_TAGS variable, but not both.

VOLUMES - List of volume-ids  
eg. ["vol-12345678"] or ["vol-12345678", "vol-87654321", ...]

VOLUME_TAGS - Dictionary of tags to use to filter the volumes. May specify multiple  
eg. {"key": "value"} or {"key1": "value1", "key2": "value2", ...}

SNAPSHOT_TAGS - Dictionary of tags to apply to the created snapshots  
eg. {"key": "value"} or {"key1": "value1", "key2": "value2", ...}

REGION - AWS regions in which the volumes exist  
eg. ["us-east-1"] or ["us-east-1", "us-west-1", ...]

## Configure Lambda function
### IAM Role Policy
Go to the IAM service in the AWS Management console. Click on Roles and click the Create Role button. Click Lambda under the 'Choose the service that will use this role' section and click the Next:Permissions button. On the 'Attach permissions policies' page, don't check any boxes and just click the Next:Review button. Name the role ec2-take-snapshots and click the Create role button. Click on the newly created role and click the Add inline policy link and click the JSON tab. Copy the contents of the iam_role_policy.json file and paste it in the box and click the Review policy button. Name the policy root and click the Create policy button.

### Create Lambda function
#### Configure function
Go to the Lambda service in the AWS Management console. Create the Create function button and on the Author from scratch page fill in the following details:
* Name: ec2-take-snapshots
* Runtime: Python 3.6
* Role: Choose an existing role
* Existing role: ec2-take-snapshots  
Click the Create function button. In the Function code box fill out:
* Handler: lambda_function.main
* Code box: paste the contents of the ec2-take-snapshots-lambda.py file  
Scroll down to the settings at the bottom. In Basic settings fill in:
* Description: An AWS Lambda function that takes EC2 snapshots
* Memory: 128
* Timeout: 1 min 0 sec  
In the code editor, configure the variables at the top of the script to your desired configuration. Click Save.

#### Event sources
In the Designer - Add triggers box click CloudWatch Events and click the CloudWatch Events box on the right. Click Create a new rule in the Rule dropdown. Fill in the following details:
* Name: ec2-take-snapshots
* Description: Run script hourly
* Schedule Expression: cron(40 * * * ? *)  
Your function will run every hour at 40 minutes. You can change the cron expression to your desired schedule. Click the Add button and then click the Save button.

#### Test function
You can test the function from the Lambda console. Click the Select a test event.. button and select Configure test events. Choose Scheduled Event from the Event template drop down. Add the following parameter to the structure "noop": "True".  This will tell the script to not actually create any snapshots, but to print that it would have. Name the Event name noop and click the Create button. Click the Test button and you will see the results of the script running in the Lambda console.

#### CloudWatch logs
You will be able to see the output when the script runs in the CloudWatch logs. Go to the CloudWatch service in the AWS Management console. Click on Logs and you will see the ec2-take-snapshots log group. Click in it and you will see a Log Stream for every time the script is executed which contains all the output of the script. Go back to the Log Groups and click the Never Expire link in the Expire Events After column of the log group row. Change the Retention period to what you feel comfortable with.