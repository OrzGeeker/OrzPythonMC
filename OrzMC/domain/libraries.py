def is_allowed_by_rules(rules, platform_type):
    if rules == None:
        return True
    for rule in rules:
        if rule == None:
            continue
        action = rule.get('action')
        os_rule = rule.get('os')
        os_name = os_rule.get('name') if os_rule else None
        if action == 'disallow' and os_name == platform_type:
            return False
        if action == 'allow' and os_name and os_name != platform_type:
            return False
    return True

def resolve_libraries(version_json_obj, platform_type):
    libs = version_json_obj.get('libraries') if version_json_obj else []
    resolved = []
    for lib in libs:
        downloads = lib.get('downloads')
        rules = lib.get('rules')
        if not is_allowed_by_rules(rules, platform_type):
            continue

        natives = lib.get('natives')
        if natives:
            platform_key = natives.get(platform_type)
            if platform_key:
                native_info = downloads.get('classifiers', {}).get(platform_key)
                if native_info:
                    resolved.append({
                        'kind': 'native',
                        'url': native_info.get('url'),
                        'sha1': native_info.get('sha1'),
                        'path': native_info.get('path')
                    })
            continue

        classifiers = downloads.get('classifiers')
        native_key = 'natives-' + platform_type
        if classifiers and native_key in classifiers:
            native_info = classifiers.get(native_key)
            if native_info:
                resolved.append({
                    'kind': 'native',
                    'url': native_info.get('url'),
                    'sha1': native_info.get('sha1'),
                    'path': native_info.get('path')
                })

        artifact = downloads.get('artifact')
        if artifact:
            path = artifact.get('path')
            if platform_type == 'windows' and path:
                path = path.replace('/','\\')
            resolved.append({
                'kind': 'artifact',
                'url': artifact.get('url'),
                'sha1': artifact.get('sha1'),
                'path': path
            })
    return resolved
