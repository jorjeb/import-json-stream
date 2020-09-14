from django.core.management.base import BaseCommand

from jsonstreamer import JSONStreamer

from sys import stdin


class Parser:
    def parse(self, data=stdin):
        self._stack = []
        self._cursor = 0
        self._key = None

        self._arr_stack = []
        self._arr_cursor = 0

        def _catch_all(event_name, *args):
            print('\t{} : {}'.format(event_name, args))

        streamer = JSONStreamer()
        streamer.add_catch_all_listener(_catch_all)
        streamer.add_listener(JSONStreamer.OBJECT_START_EVENT,
                              self._object_start)
        streamer.add_listener(JSONStreamer.OBJECT_END_EVENT,
                              self._object_end)
        streamer.add_listener(JSONStreamer.ARRAY_START_EVENT,
                              self._array_start)
        streamer.add_listener(JSONStreamer.ARRAY_END_EVENT,
                              self._array_end)
        streamer.add_listener(JSONStreamer.KEY_EVENT,
                              self._key_event)
        streamer.add_listener(JSONStreamer.VALUE_EVENT,
                              self._value)
        streamer.add_listener(JSONStreamer.ELEMENT_EVENT,
                              self._element)
        streamer.consume(data.read())
        streamer.close()

    def _object_start(self, *args):
        value = {}

        if self._key is not None:
            value = self._stack[self._cursor][self._key] = {}
        elif len(self._arr_stack) > 0:
            self._arr_stack[self._arr_cursor].append(value)

        self._stack.append(value)
        self._cursor = len(self._stack) - 1

    def _object_end(self, *args):
        self._stack.pop()
        self._key = None
        self._cursor -= 1

    def _array_start(self, *args):
        value = []

        if self._key is not None:
            value = self._stack[self._cursor][self._key] = []

        self._stack.append(value)
        self._cursor = len(self._stack) - 1
        self._arr_stack.append(value)
        self._arr_cursor = len(self._arr_stack) - 1

    def _array_end(self, *args):
        self._stack.pop()
        self._key = None
        self._cursor -= 1
        self._arr_cursor -= 1

    def _key_event(self, *args):
        self._stack[self._cursor][args[0]] = None
        self._key = args[0]

    def _value(self, *args):
        self._stack[self._cursor][self._key] = args[0]
        self._key = None

    def _element(self, *args):
        self._stack[self._cursor].append(args[0])


class Command(BaseCommand, Parser):
    help = 'Migrate data'

    def handle(self, *args, **options):
        self.level = 0

        self.stdout.write(self.style.SUCCESS('Migrating data...'))

        super(Command, self).parse()

        self.stdout.write('\n')

        self.stdout.write(self.style.SUCCESS(
            'Data has been successfully migrated.'))

    def _object_start(self, *args):
        super(Command, self)._object_start(*args)
        self.level += 1

    def _object_end(self, *args):
        super(Command, self)._object_end(*args)
        self.level -= 1

        if self.level == 0:
            model = self._stack[0].pop()
            #print(model)
