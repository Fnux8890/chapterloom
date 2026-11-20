# Engineering collects vetoes. Leave prior vetoes intact and skip the rule when the provider is absent.
scoreboard players set #provider col_api 0
function #frontier:colony_provider
execute unless score #provider col_api matches 1 run return 0
execute if score #unlocked col_api matches 1 run return 0
scoreboard players set #deny eng_api 1
tellraw @s {"text":"Press locked. Join this colony and complete Master Builder at its charter (within 12 blocks)."}
