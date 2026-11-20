function colonies:api/v1/query
execute if score #level col_api matches 2.. unless entity @s[advancements={colonies:master_builder=true}] run advancement grant @s only colonies:master_builder
