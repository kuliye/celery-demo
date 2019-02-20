from flask import render_template, redirect, url_for, jsonify, request
import time
from flask import Flask
from  celery import Celery
from home.views import home_blueprint
import random
import requests
import os

app = Flask(__name__)

app.register_blueprint(home_blueprint)

app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)


@app.route('/download/')
def download():
    return render_template('download_test.html')


@celery.task(bind=True)
def downloader(self, url, path):
    size = 0
    response = requests.get(url, stream=True)
    chunk_size = 1024
    content_size = int(response.headers['content-length']) # 总大小
    if response.status_code == 200:
        with open(path, 'wb') as file:
            for data in response.iter_content(chunk_size=chunk_size):
                file.write(data)
                size +=len(data)
                self.update_state(state='PROGRESS',meta={'current': round(float(size / content_size*100), 2)})
    return {'current': 100,'result': 'success'}

@app.route('/start_download/', methods=['POST'])
def start_download():
    url = request.form['dowloadurl']
    filename = os.path.basename(url)
    # url = 'https://dl001.liqucn.com/upload/2019/280/s/cn.gov.tax.its_1.1.3_liqucn.com.apk'
    task = downloader.apply_async((url,'download/' + filename))
    str = {'url': url_for('check_downstatus', taskid=task.id)}
    return jsonify(str)

@app.route('/check_downstatus/<taskid>')
def check_downstatus(taskid):
    task = test_task.AsyncResult(taskid)
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'current': 0,
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'current': task.info.get('current', 0),
        }
        if 'result' in task.info:
            response['result'] = task.info['result']
    else:
        # something went wrong in the background job
        response = {
            'state': task.state,
            'current': 100,
        }
    return jsonify(response)

@app.route('/')
def index():
    return render_template('index.html')

@celery.task(bind=True)
def test_task(self):
    total = 100
    count = 0
    num = 0
    for i in range(total):
        rand = random.uniform(0.5,3.0)
        time.sleep(0.5)
        count += rand

        self.update_state(state='PROGRESS',
                          meta={'current': round(count,2), 'total': i,
                                })
        if int(count) >= 100:
            count = 100
            num = i
            break
        else:
            continue
    return {'current': count, 'total': num, 'status': '任务完成!',
            'result': 100}

