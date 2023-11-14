"""
You must have an AWS account to use the Amazon Connect CTI Adapter.
Downloading and/or using the Amazon Connect CTI Adapter is subject to the terms of the AWS Customer Agreement,
AWS Service Terms, and AWS Privacy Notice.

© 2017, Amazon Web Services, Inc. or its affiliates. All rights reserved.

NOTE:  Other license terms may apply to certain, identified software components
contained within or distributed with the Amazon Connect CTI Adapter if such terms are
included in the LibPhoneNumber-js and Salesforce Open CTI. For such identified components,
such other license terms will then apply in lieu of the terms above.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import json, logging, os
import requests
import datetime

logger = logging.getLogger()
logging.basicConfig(level=logging.DEBUG, format='%(message)s')

class Salesforce:

  def __init__(self):
    self.secrets = {
        'Password': os.environ.get("SF_PASSWORD"),
        'AccessToken': os.environ.get("SF_ACCESS_TOKEN"),
        'ConsumerKey': os.environ.get("SF_CONSUMER_KEY"),
        'ConsumerSecret': os.environ.get("SF_CONSUMER_SECRET"),
    }

    self.__load_credentials()
    self.version=os.environ.get("SF_VERSION")
    self.host=os.environ.get("SF_HOST")
    self.username=os.environ.get("SF_USERNAME")

    self.login_host = self.host
    self.request = Request()
    self.auth_data = {
      'grant_type': 'password',
      'client_id': self.consumer_key,
      'client_secret': self.consumer_secret,
      'username': self.username,
      'password': self.password
    }

    if os.environ.get("SF_PRODUCTION", "").lower() == "true":
      self.set_production()

  def __load_credentials(self):
    logger.info("Loading credentials")
    self.password = self.secrets["Password"] + self.secrets["AccessToken"]
    self.consumer_key = self.secrets["ConsumerKey"]
    self.consumer_secret = self.secrets["ConsumerSecret"]
    self.auth_token = self.secrets["AuthToken"] if "AuthToken" in self.secrets else ''
    self.headers = { 
      'Authorization': 'Bearer %s' % self.auth_token,
      'Content-Type': 'application/json'
    }
    logger.info("Credentials Loaded")

  def set_production(self):
    self.login_host = 'https://login.salesforce.com'

  def search(self, query):
    logger.info("Salesforce: Search")
    url = '%s/services/data/%s/search' % (self.host, self.version)
    resp = self.makeRequest(self.request.get, **{"url": url, "params":{'q':query}})
    return resp.json()['searchRecords']

  def query(self, query):#TODO: create generator that takes care of subsequent request for more than 200 records
    logger.info("Salesforce: Query")
    url = '%s/services/data/%s/query' % (self.host, self.version)
    resp = self.makeRequest(self.request.get, **{"url": url, "params":{'q':query}})
    data = resp.json()
    for record in data['records']:
        del record['attributes']
    return data['records']

  def parameterizedSearch(self, data):#TODO: create generator that takes care of subsequent request for more than 200 records
    logger.info("Salesforce: Query")
    url = '%s/services/data/%s/parameterizedSearch' % (self.host, self.version)
    resp = self.makeRequest(self.request.post, **{"url": url, "data": data})
    data = resp.json()

    for record in data['searchRecords']:
        del record['attributes']
    return data['searchRecords']

  def update(self, sobject, sobj_id, data):
    logger.info("Salesforce: Update")
    url = '%s/services/data/%s/sobjects/%s/%s' % (self.host, self.version, sobject, sobj_id)
    resp = self.makeRequest(self.request.patch, **{"url": url, "data": data})
    return resp.status_code

  def update_by_external(self, sobject, field, sobj_id, data):
    logger.info("Salesforce: Update by external")
    url = '%s/services/data/%s/sobjects/%s/%s/%s' % (self.host, self.version, sobject, field, sobj_id)
    self.makeRequest(self.request.patch, **{"url": url, "data": data})

  def create(self, sobject, data):
    logger.info("Salesforce: Create")
    url = '%s/services/data/%s/sobjects/%s' % (self.host, self.version, sobject)
    resp = self.makeRequest(self.request.post, **{"url": url, "data": data})
    return resp.json()['id']

  def delete(self, sobject, sobject_id):
    logger.info("Salesforce: Delete")
    url = '%s/services/data/%s/sobjects/%s/%s' % (self.host, self.version, sobject, sobject_id)
    resp = self.makeRequest(self.request.delete, **{"url": url})

  def is_authenticated(self):
    return self.auth_token and self.host
  
  def makeRequest(self, requestMethod, **kwargs):
    try:
      if not self.is_authenticated():
        raise InvalidAuthTokenException("")
      return requestMethod(**kwargs, headers=self.headers)
    except InvalidAuthTokenException as e:
      # try re-fetching auth token
      logger.info("Retrieving new Salesforce OAuth token")
      headers = { 'Content-Type': 'application/x-www-form-urlencoded' }
      resp = self.request.post(url=self.login_host+"/services/oauth2/token", params=self.auth_data, headers=headers, hideData=True)
      data = resp.json()
      self.auth_token = self.secrets["AuthToken"] = data['access_token']
      self.headers = kwargs['headers'] = { 
        'Authorization': 'Bearer %s' % self.auth_token,
        'Content-Type': 'application/json'
      }
      return requestMethod(**kwargs)

class Request:
  def post(self, url, headers, data=None, params=None, hideData=False):
    logger.info('POST Requests:\nurl=%s' % url)
    if not hideData:
      logger.info("data=%s\nparams=%s" % (data, params))
    r = requests.post(url=url, data=json.dumps(data), params=params, headers=headers)
    if not hideData:
      logger.info("Response: %s" % r.text)
    return __check_resp__(r)

  def delete(self, url, headers):
    logger.info("DELETE Requests:\nurl=%s" % url)
    r = requests.delete(url=url, headers=headers)
    logger.info("Response: %s" % r.text)
    return __check_resp__(r)

  def patch(self, url, data, headers):
    logger.info("PATCH Requests:\nurl=%s\ndata=%s" % (url, data))
    r = requests.patch(url=url, data=json.dumps(data), headers=headers)
    logger.info("Response: %s" % r.text)
    return __check_resp__(r)

  def get(self, url, params, headers):
    logger.info("GET Requests:\nurl=%s\nparams=%s" % (url, params))
    r = requests.get(url=url, params=params, headers=headers)
    logger.info("Response: %s" % r.text)
    return __check_resp__(r)

def __check_resp__(resp):
  if resp.status_code // 100 == 2: 
    return resp
  
  if resp.status_code == 401:
    raise InvalidAuthTokenException("")
  
  data = resp.json()
  if 'error' in data:
    msg = "%s: %s" % (data['error'], data['error_description'])
    logger.error(msg)
    raise Exception(msg)
  
  if isinstance(data, list):
    for error in data:
      if 'message' in error:
        msg = "%s: %s" % (error['errorCode'], error['message'])
        logger.error(msg)
        raise Exception(msg)

  msg = "request returned status code: %d" % resp.status_code
  logger.error(msg)
  raise Exception(msg)

class InvalidAuthTokenException(Exception):
  pass

