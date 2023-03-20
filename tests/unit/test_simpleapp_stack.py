import aws_cdk as core
import aws_cdk.assertions as assertions

from simpleapp.simpleapp_stack import SimpleappStack

# example tests. To run these tests, uncomment this file along with the example
# resource in simpleapp/simpleapp_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = SimpleappStack(app, "simpleapp")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
