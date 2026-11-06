class_name SwgAudioSynthesizer
extends Node
## Synthétiseur Audio Galactique Procédural SWG Pre-CU (0 Dépendance Externe)
## Génère des effets sonores et jingles directement en mémoire via AudioStreamWAV.

var _player_sfx: AudioStreamPlayer = null
var _player_jingle: AudioStreamPlayer = null
var _player_loop: AudioStreamPlayer = null

var _snd_blaster: AudioStreamWAV = null
var _snd_mission: AudioStreamWAV = null
var _snd_droid: AudioStreamWAV = null
var _snd_shuttle: AudioStreamWAV = null
var _snd_speeder: AudioStreamWAV = null
var _snd_tusken: AudioStreamWAV = null
var _snd_harvest: AudioStreamWAV = null
var _snd_consume: AudioStreamWAV = null


func _ready() -> void:
	_player_sfx = AudioStreamPlayer.new()
	_player_sfx.name = "SfxPlayer"
	add_child(_player_sfx)

	_player_jingle = AudioStreamPlayer.new()
	_player_jingle.name = "JinglePlayer"
	add_child(_player_jingle)

	_player_loop = AudioStreamPlayer.new()
	_player_loop.name = "LoopPlayer"
	add_child(_player_loop)

	_build_synthetic_sounds()


func _build_synthetic_sounds() -> void:
	# 1. Tir Blaster : Glissando laser descendant 950Hz -> 180Hz avec enveloppe exponentielle
	_snd_blaster = _generate_tone_wav(0.18, 11025, func(t: float, dur: float) -> float:
		var env := exp(-t * 18.0)
		var freq := lerpf(980.0, 160.0, t / dur)
		return sin(t * freq * TAU) * env
	)

	# 2. Mission Réussie : Fanfare Galactique (Do - Mi - Sol - Do aigu)
	_snd_mission = _generate_multi_tone_wav([
		{"freq": 523.25, "dur": 0.12}, # C5
		{"freq": 659.25, "dur": 0.12}, # E5
		{"freq": 783.99, "dur": 0.15}, # G5
		{"freq": 1046.5, "dur": 0.35}  # C6
	], 11025)

	# 3. Droïde R2 : Bip-bip-sifflement à double modulation
	_snd_droid = _generate_tone_wav(0.28, 11025, func(t: float, _dur: float) -> float:
		var mod_freq := 1200.0 + sin(t * 45.0) * 400.0 + sin(t * 110.0) * 150.0
		var env := 1.0 - (t / 0.28) * 0.3
		return sin(t * mod_freq * TAU) * env
	)

	# 4. Navette Décollage : Rugissement ionique basse fréquence montant en puissance
	_snd_shuttle = _generate_tone_wav(1.4, 11025, func(t: float, dur: float) -> float:
		var p := t / dur
		var env := sin(p * PI)
		var low := sin(t * (70.0 + p * 120.0) * TAU) * 0.6
		var noise := (randf() * 2.0 - 1.0) * 0.4
		return (low + noise) * env
	)

	# 5. Speeder Moteur : Vrombissement de lévitation répété
	_snd_speeder = _generate_tone_wav(0.6, 11025, func(t: float, _dur: float) -> float:
		var hum := sin(t * 75.0 * TAU) * 0.5 + sin(t * 150.0 * TAU) * 0.25
		var flutter := sin(t * 12.0 * TAU) * 0.25
		return hum + flutter
	)
	if _snd_speeder:
		_snd_speeder.loop_mode = AudioStreamWAV.LOOP_FORWARD

	# 6. Cri Tusken : Hurlement guttural nomade binaire (URoRRuR'R'R)
	_snd_tusken = _generate_tone_wav(0.75, 11025, func(t: float, dur: float) -> float:
		var chop := sin(t * 14.0 * TAU)
		var freq := 320.0 + sin(t * 22.0) * 180.0
		var screech := sin(t * freq * TAU)
		var noise := (randf() * 2.0 - 1.0) * 0.45
		var env := sin((t / dur) * PI)
		return (screech * 0.55 + noise * 0.45) * env * (1.0 if chop > -0.2 else 0.1)
	)

	# 7. Récolte / Dépeçage : Tranchant et collecte de ressources
	_snd_harvest = _generate_tone_wav(0.32, 11025, func(t: float, dur: float) -> float:
		var env := exp(-t * 9.0)
		var whoosh := sin(t * lerpf(400.0, 150.0, t / dur) * TAU)
		var clink := sin(t * 880.0 * TAU) * 0.3
		return (whoosh + clink) * env
	)

	# 8. Consommation / Bacta : Gorgée tonifiante et impulsion revitalisante
	_snd_consume = _generate_tone_wav(0.4, 11025, func(t: float, _dur: float) -> float:
		var mod := sin(t * 28.0 * TAU) * 120.0
		var tone := sin(t * (440.0 + mod) * TAU)
		var env := (1.0 - (t / 0.4)) * 0.8
		return tone * env
	)


func play_blaster() -> void:
	if not is_inside_tree():
		return
	if _player_sfx and _snd_blaster:
		_player_sfx.stream = _snd_blaster
		_player_sfx.pitch_scale = randf_range(0.92, 1.08)
		_player_sfx.volume_db = -4.0
		_player_sfx.play()


func play_mission_complete() -> void:
	if not is_inside_tree():
		return
	if _player_jingle and _snd_mission:
		_player_jingle.stream = _snd_mission
		_player_jingle.volume_db = -2.0
		_player_jingle.play()


func play_droid() -> void:
	if not is_inside_tree():
		return
	if _player_sfx and _snd_droid:
		_player_sfx.stream = _snd_droid
		_player_sfx.pitch_scale = randf_range(0.95, 1.15)
		_player_sfx.volume_db = -3.0
		_player_sfx.play()


func play_shuttle_takeoff() -> void:
	if not is_inside_tree():
		return
	if _player_jingle and _snd_shuttle:
		_player_jingle.stream = _snd_shuttle
		_player_jingle.volume_db = -1.0
		_player_jingle.play()


func play_tusken_roar() -> void:
	if not is_inside_tree():
		return
	if _player_sfx and _snd_tusken:
		_player_sfx.stream = _snd_tusken
		_player_sfx.pitch_scale = randf_range(0.9, 1.1)
		_player_sfx.volume_db = 0.0
		_player_sfx.play()


func play_harvest() -> void:
	if not is_inside_tree():
		return
	if _player_sfx and _snd_harvest:
		_player_sfx.stream = _snd_harvest
		_player_sfx.pitch_scale = randf_range(0.95, 1.05)
		_player_sfx.volume_db = -3.0
		_player_sfx.play()


func play_consume() -> void:
	if not is_inside_tree():
		return
	if _player_sfx and _snd_consume:
		_player_sfx.stream = _snd_consume
		_player_sfx.pitch_scale = randf_range(0.98, 1.05)
		_player_sfx.volume_db = -2.0
		_player_sfx.play()


func set_speeder_sound(active: bool) -> void:
	if not is_inside_tree():
		return
	if _player_loop and _snd_speeder:
		if active:
			if not _player_loop.playing:
				_player_loop.stream = _snd_speeder
				_player_loop.volume_db = -6.0
				_player_loop.play()
		else:
			if _player_loop.playing:
				_player_loop.stop()


func _generate_tone_wav(duration: float, mix_rate: int, synth_func: Callable) -> AudioStreamWAV:
	var total_samples := int(duration * mix_rate)
	var bytes := PackedByteArray()
	bytes.resize(total_samples)

	for i in range(total_samples):
		var t := float(i) / float(mix_rate)
		var s: float = float(synth_func.call(t, duration))
		var sample_val := int(clampf(s, -1.0, 1.0) * 126.0 + 128.0)
		bytes[i] = sample_val

	var wav := AudioStreamWAV.new()
	wav.format = AudioStreamWAV.FORMAT_8_BITS
	wav.mix_rate = mix_rate
	wav.data = bytes
	return wav


func _generate_multi_tone_wav(notes: Array, mix_rate: int) -> AudioStreamWAV:
	var total_samples := 0
	for n in notes:
		total_samples += int(float(n["dur"]) * mix_rate)

	var bytes := PackedByteArray()
	bytes.resize(total_samples)
	var cursor := 0

	for n in notes:
		var freq: float = float(n["freq"])
		var dur: float = float(n["dur"])
		var samples_count := int(dur * mix_rate)

		for i in range(samples_count):
			var t := float(i) / float(mix_rate)
			var env := sin((float(i) / float(samples_count)) * PI)
			var s := sin(t * freq * TAU) * env
			var sample_val := int(clampf(s, -1.0, 1.0) * 126.0 + 128.0)
			bytes[cursor] = sample_val
			cursor += 1

	var wav := AudioStreamWAV.new()
	wav.format = AudioStreamWAV.FORMAT_8_BITS
	wav.mix_rate = mix_rate
	wav.data = bytes
	return wav
