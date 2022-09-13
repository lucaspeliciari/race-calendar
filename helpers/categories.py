from helpers.urls import *


categories = [  # replace with user preferences, if ever adding that
        {
        'name': 'Formula 1',
         'api_url': FORMULA1_URL,
         'official_website': 'https://www.formula1.com/en/racing/2022.html'
         },
          {
          'name': 'NTT IndyCar Series', 
          'api_url': INDYCAR_URL, 
          'official_website': 'https://www.indycar.com/Schedule'
          },
          {
          'name': 'Formula E', 
          'api_url': FORMULAE_URL, 
          'official_website': 'https://www.fiaformulae.com/br/championship/race-calendar'
          },
          {
          'name': 'Indy Lights', 
          'api_url': INDYLIGHTS_URL, 
          'official_website': 'https://www.indycar.com/IndyLights'
          },
          # {
          # 'name': 'MotoGP', # not working because sportradar data is different
          # 'api_url': MOTOGP_URL, 
          # 'official_website': 'https://www.motogp.com/en/calendar'
          # },
          {
          'name': 'SuperBike',
          'api_url': SUPERBIKE_URL, 
          'official_website': 'https://www.worldsbk.com/en/calendar'
          },
          # {
          # 'name': 'World Rally Championship',   # not working because sportradar data is different
          # 'api_url': WRC_URL, 
          # 'official_website': 'https://www.wrc.com/en/championship/calendar/wrc/'
          # },

          # nascar not working because sportradar data is different
          ]