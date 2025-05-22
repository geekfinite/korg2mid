# korg2mid - extract your songs from KORG M01 Music Workstation and convert them to MIDI
_I'm not a programmer, code is written by DeepSeek R1, Qwen and ChatGPT - I only fed it with information I discovered myself to create it_

![Screenshot](/readme-assets/korg.png)

**Requires MIDIUtil library to work**

If you ever wanted to preserve songs you made on your DS/3DS in Korg M01 or even improve them in an external DAW, here's a solution!
A Python script that takes raw data from your save file for KORG M01 Music Workstation and converts it to MIDI.
Expects either separate tracks from 3DS version with **.m01** extension or a dump of a savefile from DS version with **.sav** extension.

## How to dump savedata
**DS version:**
I can only speculate on this part, unfortunately, but likely you'll have to use a flashcart of some sort or use a soft-modded 3DS.
**3DS version:**
KORG M01D Music Workstation for 3DS saves files to this location on the SD card:
`sd:\\Nintendo 3DS\00000000000000000000000000000000\00000000000000000000000000000000\extdata\00000000\00000F16`
But you still have to decrypt these yourself.


Initially my idea was to just convert it to the format 3DS version expects, then use 3DS version to export MIDIs, but I decided to skip the man in the middle entirely later on (since, let's be honest, even though 3DS version allows to export your song data into MIDI, you still have to then spend time reworking the thing, rearranging the drums, and so on, and so on).
Since I don't have any programming skills, I decided to try using AI to help me flesh it out, using my notes.

I include my rough notes and original drum mappings in hopes that it could be used to develop a better idea of file structure and possibly make a better script later on.
_Notes still contain some mistakes and misconceptions, but in general they were enough to make a working script so far_
