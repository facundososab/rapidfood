def log_post_data(data):
    import os
    with open(os.path.join(os.path.dirname(__file__), 'debug.txt'), 'a') as f:
        f.write(str(data) + '\n')
