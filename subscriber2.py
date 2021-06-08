import zmq
import json
import random
import time
import datetime

class Subscriber:
    #################################################################
    # constructor
    #################################################################
    def __init__(self, own_address, topics, broker_address, 
                 indefinite=False, max_event_count=15):
        # when a subscriber is initialized. it needs to specify its topics
        self.own_address = own_address
        self.topics = topics
        self.broker_address = broker_address
        self.indefinite = indefinite
        self.max_event_count = max_event_count

        #  The zmq context
        self.context = None

        # we will use the poller to poll for incoming data
        self.poller = None

        # these are the sockets we open one for each subscription
        self.broker_reg_socket = None
        self.sub_socket_dict = {}
        
        # a list to store all the messages received
        self.received_message_list = []

    def configure(self):
        # first get the context
        print ("Subscriber::configure - set the context object")
        self.context = zmq.Context()

        # obtain the poller
        print ("Subscriber::configure - set the poller object")
        self.poller = zmq.Poller()

        # now create socket to register with broker
        print("Subscriber::configure - connect to register with broker")
        self.broker_reg_socket = self.context.socket(zmq.REQ)
        self.broker_reg_socket.connect("tcp://{0:s}:5556".format(self.broker_address))
        

    def register_sub(self):
        print("Subscriber::event - registration started")
        message_dict = {'address': self.own_address, 'topics': self.topics}
        message = json.dumps(message_dict, indent=4)
        self.broker_reg_socket.send_string(message)
        
        received_message = self.broker_reg_socket.recv_string()
        broker_port_dict = json.loads(received_message)
        
        # now create socket to receive message from broker
        for topic in self.topics:
            broker_port = broker_port_dict[topic]
            self.sub_socket_dict[topic] = self.context.socket(zmq.SUB)
            self.poller.register(self.sub_socket_dict[topic], zmq.POLLIN)
            self.sub_socket_dict[topic].connect("tcp://{0:s}:{1:d}".format(self.broker_address, broker_port))
            self.sub_socket_dict[topic].setsockopt_string(zmq.SUBSCRIBE, '')
            print("Subscriber:: Getting Topic {0:s} from Broker at {1:s}:{2:d}".format(topic, self.broker_address, broker_port))
        print("Subscriber::event - registration completed")    
        

    def notify(self):
        print ("Subscriber:event_loop - start to receive message")
        if self.indefinite:
            while True:
                events = dict(self.poller.poll())           
                for topic in self.sub_socket_dict.keys():
                    if self.sub_socket_dict[topic] in events:
                        receive_time = time.time()
                        full_message = self.sub_socket_dict[topic].recv_string() + ' Received at ' + f'{receive_time}'
                        self.received_message_list.append(full_message)
                        print(full_message)
        else:
            for i in range(self.max_event_count):
                events = dict(self.poller.poll())           
                for topic in self.sub_socket_dict.keys():
                    if self.sub_socket_dict[topic] in events:
                        receive_time = time.time()
                        full_message = self.sub_socket_dict[topic].recv_string() + ' Received at ' + f'{receive_time}'
                        self.received_message_list.append(full_message)
                        print(full_message)            

try:
    test = Subscriber(own_address='127.0.0.1', topics=['C', 'B'], 
                      broker_address='127.0.0.1',  indefinite=False, 
                      max_event_count=15)
    test.configure()
    test.register_sub()
    test.notify()
except KeyboardInterrupt:
    print('> User forced exit!')    
except Exception as e:
    print("Oops!", e.__class__, "occurred.") 