# tpb_downloader
A script to parse and download new episodes for TV series from thepiratebay

# How to use:
1. Install transmission packages including transmission-remote and transmission-daemon
2. Extend config.json with the list of your series (provide title and next_episode)
3. Run ./tpb_downloader.py or ./tpb_downloader.py --nohd (Python2)

# Current limitations:
- supports only Transmission for Linux
- no logging support (all messages returned to STDOUT)
- downloads only one episode per series per run
- downloader cannot send emails
- downloader cannot download the whole series or movies
- downloader does not work with a TV database to pull and validate the data in the config
- config.json has to be created manually in the following format (maintained by the script till final_episode):
```[
    {
        "next_episode": "S01E01", 
        "final_episode": "S01E10", 
        "next_episode_airs": "Dec/05/2014", 
        "isActive": true, 
        "title": "westworld"
    }, 
    {
        "next_episode": "S07E10", 
        "final_episode": "S07E16", 
        "next_episode_airs": "Dec/05/2014", 
        "isActive": true, 
        "title": "walking dead"
    }
]
```