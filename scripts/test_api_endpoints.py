import requests

BASE = 'http://127.0.0.1:8000'

def run_tests():
    # 1. Test root HTML
    r = requests.get(BASE + '/')
    assert r.status_code == 200, f'Root failed: {r.status_code}'
    print('[1/5] Root / served successfully (HTTP 200)')

    # 2. Test sample_image (Bridge)
    r = requests.get(BASE + '/api/sample_image?class_name=bridge')
    assert r.status_code == 200, f'sample_image failed: {r.status_code}'
    data = r.json()
    assert 'image_path' in data and 'raw_base64' in data
    bridge_path = data['image_path']
    filename = data['filename']
    print('[2/5] /api/sample_image (bridge): ' + str(filename))

    # 3. Test inspect_sample (Bridge)
    r = requests.post(BASE + '/api/inspect_sample', data={'image_path': bridge_path, 'pattern_type': 'line_space'})
    assert r.status_code == 200, f'inspect_sample failed: {r.status_code}'
    res = r.json()
    pred = res.get('predicted_class')
    conf = res.get('confidence', 0.0)
    disp = res.get('disposition')
    kdi = res.get('kdi_score')
    print('[3/5] /api/inspect_sample (bridge): Pred=' + str(pred) + ', Conf=' + f'{conf:.2%}' + ', KDI=' + str(kdi) + ', Disp=' + str(disp))
    assert pred == 'bridge'
    assert disp == 'SCRAP'
    assert 'visuals' in res and 'overlay' in res['visuals'] and 'heatmap' in res['visuals']
    overlay_len = len(res['visuals']['overlay'])
    sop_cited = res['advisor'].get('cited_sop_ids')
    rc = res['advisor'].get('root_cause_hypothesis', '')[:70]
    print('      -> Overlay & Heatmap visuals generated (' + str(overlay_len) + ' chars)')
    print('      -> SOP cited: ' + str(sop_cited))
    print('      -> Root cause: ' + str(rc) + '...')

    # 4. Test sample_image & inspect_sample (Clean)
    r = requests.get(BASE + '/api/sample_image?class_name=clean')
    clean_path = r.json()['image_path']
    r = requests.post(BASE + '/api/inspect_sample', data={'image_path': clean_path, 'pattern_type': 'line_space'})
    res_clean = r.json()
    pred_c = res_clean.get('predicted_class')
    conf_c = res_clean.get('confidence', 0.0)
    disp_c = res_clean.get('disposition')
    kdi_c = res_clean.get('kdi_score')
    sop_c = res_clean['advisor'].get('cited_sop_ids')
    rc_c = res_clean['advisor'].get('root_cause_hypothesis', '')
    print('[4/5] /api/inspect_sample (clean): Pred=' + str(pred_c) + ', Conf=' + f'{conf_c:.2%}' + ', KDI=' + str(kdi_c) + ', Disp=' + str(disp_c))
    assert pred_c == 'clean'
    assert disp_c == 'PASS'
    print('      -> Clean SOP cited: ' + str(sop_c))
    print('      -> Clean root cause: ' + str(rc_c))

    # 5. Test inspect_upload (Upload file)
    with open(bridge_path, 'rb') as f:
        files = {'file': (filename, f, 'image/png')}
        r = requests.post(BASE + '/api/inspect', files=files, data={'pattern_type': 'line_space'})
    assert r.status_code == 200
    res_upload = r.json()
    pred_u = res_upload.get('predicted_class')
    conf_u = res_upload.get('confidence', 0.0)
    disp_u = res_upload.get('disposition')
    print('[5/5] /api/inspect (upload): Pred=' + str(pred_u) + ', Conf=' + f'{conf_u:.2%}' + ', Disp=' + str(disp_u))
    assert pred_u == 'bridge'

    print('\n======================================================')
    print('ALL 5 LIVE ENDPOINT TESTS PASSED COMPLETELY!')
    print('======================================================')

if __name__ == '__main__':
    run_tests()

def test_all_classes():
    for cls in ['particle', 'scratch', 'nuisance_charging', 'nuisance_jitter']:
        r1 = requests.get(BASE + '/api/sample_image?class_name=' + cls)
        path = r1.json()['image_path']
        r2 = requests.post(BASE + '/api/inspect_sample', data={'image_path': path, 'pattern_type': 'line_space'})
        res = r2.json()
        pred = res.get('predicted_class')
        conf = res.get('confidence', 0.0)
        disp = res.get('disposition')
        bbox = res.get('bbox')
        print(cls.upper() + ': Pred=' + str(pred) + ', Conf=' + f'{conf:.2%}' + ', Disp=' + str(disp) + ', BBox=' + str(bbox))

if __name__ == '__main__':
    test_all_classes()
