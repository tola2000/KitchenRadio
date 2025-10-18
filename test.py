from mpd import MPDClient

client = MPDClient()
client.connect("192.168.1.4", 6600)

playlists = client.listplaylists()
client.load("Willy")
client.play()

for p in playlists:
    print(p['playlist'])

client.close()
client.disconnect()