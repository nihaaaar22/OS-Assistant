  
    
# class base_env:

      

#     def stop(self):
#             """
#             Stops the execution of all active languages.
#             """        
#             for language in self._active_languages.values():
#                 language.stop()

#     def terminate(self):
#         """
#         Terminates all active language environments.
#         """        
#         for language_name in list(self._active_languages.keys()):
#             language = self._active_languages[language_name]
#             if (
#                 language
#             ):  # Not sure why this is None sometimes. We should look into this
#                 language.terminate()
#             del self._active_languages[language_name]