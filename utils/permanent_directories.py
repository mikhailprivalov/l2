# permanent_directories = {"Пол пациента":
#                    [{"code": 1, "title": "Мужской"}, {"code": 2, "title": "Женский"}],
#                "Вид места жительства":
#                    [{"code": 1, "title": "Мужской"}, {"code": 2, "title": "Женский"}],
#                "Виды медицинской документации":
#                    [{"code": 13, "title": "Медицинское свидетельство о смерти"}],
#                "Родственные и иные связи":
#                    [{"code": 1, "title": "Мать"}],
#                "Семейное положение":
#                    [{"code": 1, "title": "состоит в зарегистрированном браке"}, {"code": 2, "title": "не состоит в зарегистрированном браке"},
#                     {"code": 3, "title": "неизвестно"}],
#                "Классификатор образования для медицинских свидетельств":
#                    [{"code": 1, "title": "профессиональное: высшее"},
#                     {"code": 2, "title": "профессиональное: неполное высшее"},
#                     {"code": 3, "title": "профессиональное: среднее"},
#                     {"code": 4, "title": "профессиональное: начальное"},
#                     {"code": 5, "title": "общее: среднее (полное)"},
#                     {"code": 6, "title": "общее: основное"},
#                     {"code": 7, "title": "общее: начальное"},
#                     {"code": 8, "title": "не имеет образования"},
#                     {"code": 9, "title": "неизвестно"},
#                     ],
#                "Занятость":
#                    [{"code": 1, "title": "занятость в экономике: руководители и специалистам высшего уровня квалификаци"},
#                     {"code": 2, "title": "занятость в экономике: прочие специалисты"},
#                     {"code": 3, "title": "занятость в экономике: квалифицированные рабочие"},
#                     {"code": 4, "title": "занятость в экономике: неквалифицированные рабочие"},
#                     {"code": 5, "title": "занятость в экономике: занятые на военной службе"},
#                     {"code": 6, "title": "отсутствие занятости в экономике: пенсионеры"},
#                     {"code": 7, "title": "отсутствие занятости в экономике: студенты и учащиеся"},
#                     ],
#                "Вид медицинского свидетельства о смерти":
#                    [{"code": 1, "title": "окончательное"},
#                     {"code": 2, "title": "предварительное"},
#                     {"code": 3, "title": "взамен предварительногое"},
#                     {"code": 4, "title": "взамен окончательного"},
#                     ],
#                "Типы мест наступления смерти":
#                    [{"code": 1, "title": "на месте происшествия"},
#                     {"code": 2, "title": "в машине скорой помощи"},
#                     {"code": 3, "title": "в стационаре"},
#                     {"code": 4, "title": "дома"},
#                     {"code": 4, "title": "в другом месте"},
#                     {"code": 5, "title": "неизвестно"},
#                     ],
#                "Род причины смерти":
#                    [{"code": 1, "title": "от заболевания"},
#                     {"code": 2, "title": "от несчастного случая, не связанного с производством"},
#                     {"code": 3, "title": "от несчастного случая, связанного с производством"},
#                     {"code": 4, "title": "убийства"},
#                     {"code": 5, "title": "самоубийства"},
#                     {"code": 6, "title": "в ходе военных действий"},
#                     {"code": 7, "title": "в ходе террористических д"},
#                     ],
#                "Основания для установления причины смерти":
#                    [{"code": 1, "title": "осмотр трупа"},
#                     {"code": 2, "title": "записи в медицинской документации"},
#                     {"code": 3, "title": "предшествующее наблюдение за больным(ой)"},
#                     {"code": 4, "title": "вскрытие"},
#                     ],
#                "Связь смерти с ДТП":
#                    [{"code": 1, "title": "в течение 30 суток"},
#                     {"code": 2, "title": "из них в течение 7 суток"},
#                     ],
#                "Связь смерти с беременностью":
#                    [{"code": 1, "title": "смерть беременной (независимо от срока и локализации)"},
#                     {"code": 2, "title": "в процессе родов (аборта)"},
#                     {"code": 3, "title": "в течение 42 дней после окончания беременности, родов (аборта)"},
#                     {"code": 4, "title": "в течение 43-365 дней после окончания беременности, родов"},
#                     ],
#                }

permanent_directories = {"Пол пациента": ["1-Мужской", "2-Женский"],
                         "Вид места жительства": ["1-Мужской", "2-Женский"],
                         "Виды медицинской документации": ["13-Медицинское свидетельство о смерти"],
                         "Родственные и иные связи": ["1-Мать"],
                         "Семейное положение": ["1-состоит в зарегистрированном браке", "2-не состоит в зарегистрированном браке", "3-неизвестно"],
                         "Классификатор образования для медицинских свидетельств":
                             ["1-профессиональное: высшее", "2-профессиональное: неполное высшее", "3-профессиональное: среднее", "4-профессиональное: начальное",
                              "5-общее: среднее (полное)", "6-общее: основное",
                              "7-общее: начальное", "8-не имеет образования", "9-неизвестно",
                              ],
                         "Занятость":
                             ["1-занятость в экономике: руководители и специалистам высшего уровня квалификаци", "2-занятость в экономике: прочие специалисты",
                              "3-занятость в экономике: квалифицированные рабочие", "4-занятость в экономике: неквалифицированные рабочие",
                              "5-занятость в экономике: занятые на военной службе", "6-отсутствие занятости в экономике: пенсионеры",
                              "7-отсутствие занятости в экономике: студенты и учащиеся",
                              ],
                         "Вид медицинского свидетельства о смерти":
                             ["1-окончательное",
                              "2-предварительное",
                              "3-взамен предварительногое",
                              "4-взамен окончательного",
                              ],
                         "Типы мест наступления смерти":
                             ["1-на месте происшествия",
                              "2-в машине скорой помощи",
                              "3-в стационаре",
                              "4-дома",
                              "5-в другом месте",
                              "6-неизвестно",
                              ],
                         "Род причины смерти":
                             ["1-от заболевания",
                              "2-от несчастного случая, не связанного с производством",
                              "3-от несчастного случая, связанного с производством",
                              "4-убийства",
                              "5-самоубийства",
                              "6-в ходе военных действий",
                              "7-в ходе террористических д",
                              ],
                         "Основания для установления причины смерти":
                             ["1-осмотр трупа",
                              "2-записи в медицинской документации",
                              "3-предшествующее наблюдение за больным(ой)",
                              "4-вскрытие",
                              ],
                         "Связь смерти с ДТП":
                             ["1-в течение 30 суток",
                              "2-из них в течение 7 суток",
                              ],
                         "Связь смерти с беременностью":
                             ["1-смерть беременной (независимо от срока и локализации)",
                              "2-в процессе родов (аборта)",
                              "3-в течение 42 дней после окончания беременности, родов (аборта)",
                              "4-в течение 43-365 дней после окончания беременности, родов",
                              ],
                         }
