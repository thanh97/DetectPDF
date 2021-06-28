import os
from flask import Flask, request, render_template, stream_with_context
import re
import pdfplumber
import pandas as pd
from collections import namedtuple
from werkzeug.datastructures import Headers
from werkzeug.wrappers import Response
app= Flask(__name__)


@app.route('/', methods=['GET'])
def upload_file():
   return render_template('home.html')

def processpdf(file):
  lines = []
  total_check = 0
  Line = namedtuple('Line', 'company_id company_name doctype reference currency voucher inv_date due_date open_amt_tc open_amt_bc current months1 months2 months3')
  company_re = re.compile(r'(V\d+) (.*) Phone:')
  line_re = re.compile(r'\d{2}/\d{2}/\d{4} \d{2}/\d{2}/\d{4}')

  with pdfplumber.open(file) as pdf:
    for page in pdf.pages:
      text = page.extract_text()
      for line in text.split('\n'):
        # print(line)
        comp = company_re.search(line)
        if comp:
          vend_no, vend_name = comp.group(1), comp.group(2)

        elif line.startswith('INVOICES'):
          doctype = 'INVOICE'

        elif line.startswith('CREDITNOTES'):
          doctype = 'CREDITNOTE'

        elif line_re.search(line):
          items = line.split()
          lines.append(Line(vend_no, vend_name, doctype, *items))

        elif line.startswith('Supplier total'):
          tot = float(line.split()[2].replace(',', ''))
          total_check += tot
  df = pd.DataFrame(lines)
  # df.head()

  # df.info()

  df['inv_date'] = pd.to_datetime(df['inv_date'])
  df['due_date'] = pd.to_datetime(df['due_date'])
  for col in df.columns[-6:]:
    df[col] = df[col].map(lambda x: float(str(x).replace(',', '')))

  df['open_amt_bc'].sum()

  # total_check

  return df

@app.route('/upload', methods=['GET','POST'])
def upload():
  if request.method == 'POST':
    files = request.files['files']
    data = processpdf(files)
    # data.to_csv(index=False)
    headers = Headers()
    headers.set('Content-Disposition', 'attachment', filename='log.csv')

  return Response(stream_with_context(data.to_csv(index=False)), mimetype='text/csv', headers=headers)



