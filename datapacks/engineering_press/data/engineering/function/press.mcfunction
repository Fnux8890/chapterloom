# Evaluate every installed rule before inspecting or consuming ingredients.
scoreboard players set @s eng_press 0
execute unless block ~ ~-1 ~ minecraft:smithing_table run return run tellraw @s {"text":"Stand on a smithing table to use the field press."}
scoreboard players set #deny eng_api 0
function #engineering:api/v1/press_checks
execute if score #deny eng_api matches 1.. run return 0
execute store result score #iron eng_api run clear @s minecraft:iron_ingot 0
execute store result score #sticks eng_api run clear @s minecraft:stick 0
execute unless score #iron eng_api matches 6.. run return run tellraw @s {"text":"The press needs six iron ingots."}
execute unless score #sticks eng_api matches 1.. run return run tellraw @s {"text":"The press needs one stick."}
clear @s minecraft:iron_ingot 6
clear @s minecraft:stick 1
give @s minecraft:rail 24
advancement grant @s only engineering:first_batch
