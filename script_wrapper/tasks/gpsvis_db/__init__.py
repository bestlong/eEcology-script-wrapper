import colander
from celery.utils.log import get_task_logger
from script_wrapper.tasks import MatlabTask
from script_wrapper.models import getGPSCount
from script_wrapper.validation import validateRange
from script_wrapper.validation import iso8601Validator

logger = get_task_logger(__name__)


class Tracker(colander.MappingSchema):
    id = colander.SchemaNode(colander.Int())
    color = colander.SchemaNode(colander.String())
    size = colander.SchemaNode(colander.String())
    speed = colander.SchemaNode(colander.Int())


class Trackers(colander.SequenceSchema):
    tracker = Tracker()


class Schema(colander.MappingSchema):
    start = colander.SchemaNode(colander.String(), validator=iso8601Validator)
    end = colander.SchemaNode(colander.String(), validator=iso8601Validator)
    trackers = Trackers()
    valid_alt_modes = ['absolute', 'clampToGround', 'relativeToGround']
    alt = colander.SchemaNode(colander.String(), validator=colander.OneOf(valid_alt_modes))


class GpsVisDB(MatlabTask):
    """Matlab script which generate KMZ file and statistics plot
    """
    name = 'gpsvis_db'
    label = "KMZ and Plot"
    title = """Generate KMZ file and statistics plot"""
    script = 'run_stefanoe.sh'
    matlab_version = '2012b'
    MAX_FIX_COUNT = 50000
    MAX_FIX_TOTAL_COUNT = 50000

    def run(self, db_url, start, end, alt, trackers):
        # prepare arguments

        tracker_ids = []
        speeds = []
        colors = []
        sizes = []
        for tracker in trackers:
            tracker_ids.append(tracker['id'])
            colors.append(tracker['color'])
            sizes.append(tracker['size'])
            speeds.append(tracker['speed'])

        # TODO pass tracker_ids as '[1 2]' and in Matlab eval
        # See http://blogs.mathworks.com/loren/2011/01/06/matlab-data-types-as-arguments-to-standalone-applications/
        db_url = self.local_db_url(db_url)
        db_name = self.sslify_dbname(db_url)

        # execute
        result = super(GpsVisDB, self).run(db_url.username,
                                           db_url.password,
                                           db_name,
                                           db_url.host,
                                           self.list2vector_string(tracker_ids),
                                           self.list2vector_string(colors),
                                           start,
                                           end,
                                           alt,
                                           self.list2cell_array_string(sizes),
                                           self.list2vector_string(speeds),
                                           )

        result['query'] = {'start': start,
                           'end': end,
                           'alt': alt,
                           'trackers': trackers,
                           }

        return result

    def convert_colors(self, tracker):
        """Matlab script expects colortable identifier, so map color to id"""
        valid_colors = ['FFFF50',
                        'F7E8AA',
                        'FFA550',
                        '5A5AFF',
                        'BEFFFF',
                        '8CFF8C',
                        'FF8CFF',
                        'AADD96',
                        'FFD3AA',
                        'C6C699',
                        'E5BFC6',
                        'DADADA',
                        'C6B5C4',
                        'C1D1BF',
                        '000000'
                        ]
        colorid = valid_colors.index(tracker['color']) + 1
        return colorid

    def formfields2taskargs(self, fields, db_url):
        schema = Schema()
        taskargs = schema.deserialize(fields)

        trackers = taskargs['trackers']

        # Test if selection will give results
        total_gps_count = 0
        for tracker in trackers:
            gps_count = getGPSCount(db_url, tracker['id'], taskargs['start'], taskargs['end'])
            total_gps_count += gps_count
            validateRange(gps_count, 0, self.MAX_FIX_COUNT, tracker['id'])
            tracker['color'] = self.convert_colors(tracker)
        validateRange(total_gps_count, 0, self.MAX_FIX_TOTAL_COUNT)

        taskargs['db_url'] = db_url
        return taskargs
