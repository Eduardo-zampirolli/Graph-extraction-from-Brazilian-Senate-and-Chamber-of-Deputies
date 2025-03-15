
library(senatebR)

df_partidos <- obter_dados_partidos()
write.csv(partidos, "partido.csv")
