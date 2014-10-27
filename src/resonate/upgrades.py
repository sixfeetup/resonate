import logging


def enable_subtyper_for_syndication(context):
    logger = logging.getLogger(__name__)
    context.runImportStepFromProfile('profile-resonate:default', 'componentregistry')
    logger.warn('resonate subtypers enabled')


def add_proxy_content_type(context):
    logger = logging.getLogger(__name__)
    context.runImportStepFromProfile('profile-resonate:default', 'typeinfo')
    logger.warn('resonate.proxy type enabled')
