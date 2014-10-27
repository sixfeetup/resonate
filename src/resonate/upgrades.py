import logging


def enable_subtyper_for_syndication(context):
    logger = logging.getLogger(__name__)
    context.runImportStepFromProfile('profile-nd.syndication:default', 'componentregistry')
    logger.warn('nd.syndication subtypers enabled')


def add_proxy_content_type(context):
    logger = logging.getLogger(__name__)
    context.runImportStepFromProfile('profile-nd.syndication:default', 'typeinfo')
    logger.warn('nd.syndication.proxy type enabled')
