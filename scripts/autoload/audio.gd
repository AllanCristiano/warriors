extends Node
## Toca efeitos sonoros (com pool de players) e musica com crossfade.

const DIR := "res://assets/audio/"
var _cache := {}
var _pool: Array[AudioStreamPlayer] = []
var _music: AudioStreamPlayer
var _music_name := ""


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for i in 12:
		var p := AudioStreamPlayer.new()
		add_child(p)
		_pool.append(p)
	_music = AudioStreamPlayer.new()
	_music.volume_db = -8.0
	add_child(_music)
	_music.finished.connect(func(): _music.play())


func _stream(sname: String) -> AudioStream:
	if not _cache.has(sname):
		var path := DIR + sname + ".wav"
		_cache[sname] = load(path) if ResourceLoader.exists(path) else null
	return _cache[sname]


func play(sname: String, volume_db := 0.0, pitch_var := 0.08) -> void:
	var s := _stream(sname)
	if s == null:
		return
	for p in _pool:
		if not p.playing:
			p.stream = s
			p.volume_db = volume_db
			p.pitch_scale = 1.0 + randf_range(-pitch_var, pitch_var)
			p.play()
			return


func music(mname: String) -> void:
	if mname == _music_name:
		return
	_music_name = mname
	var s := _stream(mname)
	var tw := create_tween()
	if _music.playing:
		tw.tween_property(_music, "volume_db", -40.0, 0.5)
	tw.tween_callback(func():
		_music.stream = s
		_music.volume_db = -8.0
		if s: _music.play()
		else: _music.stop())
