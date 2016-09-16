import tornado.ioloop
a = tornado.ioloop.IOLoop.instance().run_sync
from va_scheduler import datastore
c = datastore.ConsulStore()
a(lambda: c.get('admins'))
