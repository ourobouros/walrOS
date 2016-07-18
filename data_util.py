import os
from enum import Enum

from apiclient import discovery
import httplib2
import oauth2client
from oauth2client import client
from oauth2client import tools

TEST_SPREADSHEET_ID = '1oDoWhImR3huPhwmmIZpGJFZybKOW6O07dMbha4O1mIE'
TEST_WORKSHEET_ID = 0

class Spreadsheet(object):

  def __init__(self, spreadsheet_id):
    self.spreadsheet_id_ = spreadsheet_id
    self.sheets_ = GetSpreadsheets()

  def GetWorksheet(self, worksheet_id):
    return Worksheet(self.spreadsheet_id_, worksheet_id)

  def GetRanges(self, ranges, fields):
    return self.sheets_.get(spreadsheetId=self.spreadsheet_id_,
                               includeGridData=False, ranges=ranges,
                               fields=fields).execute()

  def BatchUpdate(self, batch_requests):
    return self.sheets_.batchUpdate(spreadsheetId=self.spreadsheet_id_,
                                    body={'requests': batch_requests}).execute()

class Worksheet(object):

  def __init__(self, spreadsheet_id, worksheet_id):
    self.spreadsheet_id_ = spreadsheet_id
    self.worksheet_id_ = worksheet_id
    self.sheets_ = GetSpreadsheets()

  def NewInsertRowsBatchRequest(self, start_index, num_rows):
    return {
      'insertDimension': {
        'range': {
            'sheetId': self.worksheet_id_,
            'dimension': 'ROWS',
            'startIndex': start_index - 1,
            'endIndex': start_index + num_rows - 1,
        },
      },
    }

  def NewMergeRange(self, start_row, end_row, start_col, end_col):
    return {
      "startRowIndex": start_row - 1,
      "endRowIndex": end_row,
      "startColumnIndex": start_col - 1,
      "endColumnIndex": end_col,
      "sheetId": self.worksheet_id_,
    }

  def NewMergeCellsBatchRequest(self, merge_range):
    return {
      'mergeCells': {
        'mergeType': 'MERGE_ALL',
        'range': merge_range
      }
    }

  class UpdateCellsMode(Enum):
    string = 'stringValue'
    number = 'numberValue'
    formula = 'formulaValue'

  def NewUpdateCellBatchRequest(self, row, col, value,
                                update_cells_mode=UpdateCellsMode.string):
    return {
      'updateCells': {
        'fields': 'userEnteredValue',
        'start': {  # Zero-based indexing here.
          'rowIndex': row - 1,
          'columnIndex': col - 1,
          'sheetId': self.worksheet_id_,
        },
        'rows': [
          {
            'values': {
              'userEnteredValue': {
                update_cells_mode.value: value,
              },
            },
          },
        ],
      },
    }

# -- Authentication --

def memoize(init_fn):
  """Decorator to memoize initialization"""
  obj = []
  def wrapper_fn():
    if len(obj) == 0:
      obj.append(init_fn())
    return obj[0]

  return wrapper_fn


@memoize
def GetSpreadsheets():
  credentials = GetCredentials()
  http = credentials.authorize(httplib2.Http())
  discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?version=v4')
  service = discovery.build('sheets', 'v4', http=http,
                            discoveryServiceUrl=discoveryUrl)
  return service.spreadsheets()

def GetCredentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is run to obtain the new credentials.

    Returns:
        The obtained credentials.
    """
    credential_dir = os.path.join(os.path.expanduser('~'), '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'sheets.googleapis.com-walros.json')

    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILEPATH,
                                              PERMISSION_SCOPES)
        flow.user_agent = APPLICATION_NAME

        import argparse
        flags_namespace = argparse.Namespace()
        setattr(flags_namespace, 'auth_host_name', 'localhost')
        setattr(flags_namespace, 'logging_level', 'ERROR')
        setattr(flags_namespace, 'noauth_local_webserver', False)
        setattr(flags_namespace, 'auth_host_port', [8080, 8090])
        credentials = tools.run_flow(flow, store, flags_namespace)
        print('Storing credentials to ' + credential_path)
    return credentials

# -- Helper Functions --

if __name__ == '__main__':
  sheet = Spreadsheet(TEST_SPREADSHEET_ID)
  worksheet = sheet.GetWorksheet(TEST_WORKSHEET_ID)

  requests = []
  requests.append(worksheet.NewInsertRowsBatchRequest(4, 2))
  sheet.BatchUpdate(requests)