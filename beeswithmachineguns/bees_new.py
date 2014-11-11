"""based on beeswithmachineguns

* separated configuration and core functionality

* output is logged instead of printed

* class based approach
  (two reasons:
    * ease testing
    * functionality easily adjustable by by overwriting methods

* thrown out subnet stuff, as I don't understand the currrent implementation
  (seems somewhat nonsensical to me ...)
"""
import logging
import os

import boto
import boto.ec2
from plumbum.path import LocalPath, LocalWorkdir

import beeswithmachineguns.lib as beelib


log = logging.getLogger(__name__)


class Beekeeper(object):
    def __init__(self):
        self.bees = None
        self.reservation = None

    def activate_swarm(self):
        if self.hive.isActive:
            log.warning("hive is up already: %s", self.hive.asDict)
            # todo get reservation from self.hive.reservationId
            return

        self.reserve_swarm()
        while not self.swarmIsActive:
            log.info('waiting for bees to load their machine guns... '
                     '%s bees are ready', self.activeBeesIds)
        self.connection.create_tags(self.activeBeesIds, {"Name": "a bee!"})
        self.hive.reservationId = self.reservation.id
        self.hive.activate()
        log.info('The swarm assembled %i bees', len(self.activeBeesIds))

    def reserve_swarm(self):
        if not self.config.keyPath:
            raise beelib.BeeSting("key %s not found" % (self.config.keyPath))

        log.info('attempting to call up %s bees', self.config.numberOfBees)
        self.reservation = self.connection.run_instances(
            image_id=self.config.instanceId,
            min_count=self.config.numberOfBees,
            max_count=self.config.numberOfBees,
            key_name=self.config.keyName,
            security_groups=[self.config.securityGroup],
            instance_type=self.config.instanceType,
            placement=None,
            subnet_id='')

    def swarmIsActive(self):
        return len(self.activeBeesIds) == self.config.numberOfBees

    @property
    def activeBeesIds(self):
        if not self.reservation:
            return []

        instanceIds = []
        for instance in self.reservation.instances:
            instance.update()
            if instance.state == 'running':
                instanceIds.append(instance.id)
        return instanceIds

    @beelib.cached_property
    def hive(self):
        return CurrentHive()

    @beelib.cached_property
    def config(self):
        return ProjectConfig()

    @beelib.cached_property
    def connection(self):
        return boto.ec2.connect_to_region(self.config.region)


class ProjectConfig(beelib.JsonConfigger):
    CONFIG = 'beesconfig.json'
    """Global configuration"""
    KEY_NAME_PREFIX = "aws-ec2"
    KEY_EXT = '.pem'
    DEFAULT_SECURITY_GROUP = 'default'
    DEFAULT_ZONE = 'us-east-1d'
    DEFAULT_INSTANCE_ID = 'ami-ff17fb96'
    DEFAULT_INSTANCE_TYPE = 't1.micro'
    DEFAULT_NUMBER_OF_BEES = 10

    def __init__(self):
        super(ProjectConfig, self).__init__(self.CONFIG)
        self._keyContainerPaths = [self._path.dirname,
                                   LocalPath(os.getenv('HOME')) / '.ssh']
        self.securityGroup = self.DEFAULT_SECURITY_GROUP
        self.zone = self.DEFAULT_ZONE
        self.instanceId = self.DEFAULT_INSTANCE_ID
        self.numberOfBees = self.DEFAULT_NUMBER_OF_BEES
        self.instanceType = self.DEFAULT_INSTANCE_TYPE

    @property
    def region(self):
        """ region = zone without last letter """
        return self.zone[:-1]

    @beelib.cached_property
    def keyPath(self):
        candidates = [path / (self.keyName + self.KEY_EXT)
                      for path in self._keyContainerPaths]
        for candidate in candidates:
            if candidate.exists():
                return candidate

        log.warning("no key found in %s", candidates)

    @property
    def keyName(self):
        return "%s-%s" % (self.KEY_NAME_PREFIX, self.region)


class CurrentHive(beelib.JsonConfigger):
    CONFIG = 'current_hive.json'
    """configuration of an active bee hive (autogenerated)"""

    def __init__(self):
        super(CurrentHive, self).__init__(self.CONFIG)
        self.username = ''
        self.zone = ''
        self.beesIds = ''

        self.reservationId = None

    def activate(self):
        self.save_config()

    @property
    def isActive(self):
        return self._path.exists()


class LoggingConfig(object):
    NAME = 'bees'

    def __init__(self):
        self.workPath = LocalWorkdir()
        self.localLogPath = None
        """:type: LocalPath"""

    def init_logging(self, logLevel=logging.INFO, logToFile=True):
        log.setLevel(logLevel)
        self.localLogPath = self.workPath / (self.NAME + '.log')
        fmt = ('%(asctime)s %(name)s %(funcName)s:%(lineno)d '
               '%(levelname)s : %(message)s')
        logging.basicConfig(format=fmt)
        if logToFile:
            fh = logging.FileHandler(filename=str(self.localLogPath))
            fh.setFormatter(logging.Formatter(fmt))
            log.addHandler(fh)
        log.name = self.NAME if log.name == '__main__' else log.name
        log.debug("working in %s", self.workPath)


def main():
    #ProjectConfig.DEFAULT_NUMBER_OF_BEES = 1
    pc = CurrentHive()
    pc.beesIds = [1, 2, 3]
    print pc.asDict
    pc.save_config()
    exit()
    bk = Beekeeper()
    bk.activate_swarm()


if __name__ == '__main__':
    workPath = LocalWorkdir()
    workPath.chdir('../tests/fake_project_dir')
    log.info('working in %s', workPath)
    logCnf = LoggingConfig()
    logCnf.init_logging(logLevel=logging.DEBUG)
    main()

    # time.sleep(0.01)
    # for k, v in cnf.__dict__.items():
    #     print k, v
    # print cnf.beesIds
