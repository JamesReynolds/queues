FROM netdata/netdata

## Add information to netdata
COPY queue.chart.py /usr/libexec/netdata/python.d/
COPY queue.conf /usr/lib/netdata/conf.d/python.d/

## Ensure that ownership and python modules are present
RUN chown root:netdata /usr/lib/netdata/conf.d/python.d/queue.conf /usr/libexec/netdata/python.d/queue.chart.py /usr/libexec/netdata/plugins.d/python.d.plugin && \
    apk add --no-cache uwsgi-python3 python3 nginx shadow && \
    pip3 install --no-cache-dir flask pika retrying pyyaml

## Copy start up scripts and example app
COPY app.py start.sh /

## Expose ports and entrypoint
EXPOSE 19999
ENTRYPOINT /start.sh
