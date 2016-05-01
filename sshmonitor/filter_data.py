
def filter_elements_from_dict(input, filteroptions=None):
    """Filters all elements from dictioarny which are in the filteroptions
    :param input: dictionary of list of dictionaries
    :param filteroptions: list of keys which should be deleted

    :return updated dictionary
    """
    assert (isinstance(input, dict))
    if filteroptions is None:
        return input
    import logging
    log = logging.getLogger(__name__)
    assert (isinstance(filteroptions, list))
    for (key, val) in input.items():
        if val is []:
            continue
        for i, r in enumerate(val):
            if not isinstance(r, dict):
                log.warning('Element is not a dict and it should be one: {0}'.format(val))
                continue
            available_keys = r.keys()
            keys_to_delete = [x for x in available_keys if x not in filteroptions]
            if r is None:
                continue
            for f in keys_to_delete:
                del input[key][i][f]
    return input


def convert_list_of_dicts_to_list(list_of_dicts, filteroptions):
    assert (isinstance(list_of_dicts, dict))
    import logging
    log = logging.getLogger(__name__)

    def convert_list(classmembers):
        if len(classmembers) == 0:
            return dict()
        keyname_list = list(classmembers[0].keys())
        ids = [filteroptions.index(x) for x in keyname_list]
        sorted_keys = [line for (id, line) in sorted(zip(ids, keyname_list))]
        header = sorted_keys
        body = []
        for row in classmembers:
            keyname_list = list(row.keys())
            ids = [filteroptions.index(x) for x in keyname_list]

            row_values = row.values()
            sorted_values = [line for (id, line) in sorted(zip(ids, row_values))]
            body.append(sorted_values)
        return dict(header=header, body=body)

    updated_result = {}
    errors = []
    for (classkey, classmembers) in list_of_dicts.items():
        import re
        log = logging.getLogger(__name__)
        if re.search('^error', classkey):
            log.info('Skipping classkey {0}, because it matches the regex \'^error\''.format(classkey))
            updated_result[classkey] = classmembers
            continue

        if len(classmembers) >= 1 and isinstance(classmembers, list):
            updated_result[classkey] = convert_list(classmembers)
        else:
            if classmembers:
                log.error(classmembers)
                errors.append(classmembers)

            updated_result[classkey] = dict(header=[], body=[])
    if errors:
        updated_result['error'] = errors
    return updated_result