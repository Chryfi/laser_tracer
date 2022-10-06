# Laser Tracer
This script allows to create paths from an emitting object to a collection of trackers using a defined velocity and motionblur.

The first keyframe of the respective tracker will be used as impact time.

This script allows to define a constant velocity and the motionblur which should be used for rendering (Start on Frame).

The script will find the path with the minimum difference to the impact point under the restriction of the constant velocity.
Using the motionblur it will adjust and optimise the path end so when rendering, the tip of the object with motionblur will be at the impact point. Note that this will cause the velocity of the object to slightly deviate from the defined velocity.
