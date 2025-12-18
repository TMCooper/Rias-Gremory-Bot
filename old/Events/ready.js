const Discord = require("discord.js")
const loadDatabase = require("../Loader/loadDatabase")
const loadSlashCommands = require("../Loader/loadSlashCommands")

module.exports = async bot => {

    bot.db = await loadDatabase()
    bot.db.connect(function (err) {
        if(err) console.log(err)
        console.log("Base de données connectée !")
    })

    await loadSlashCommands(bot)

    console.log(`${bot.user.tag} est bien en ligne !`)
}