import logging


def add_proxy_content_type(context):
    logger = logging.getLogger(__name__)
    context.runImportStepFromProfile('profile-resonate:default', 'typeinfo')
    logger.warn('resonate.proxy type enabled')
