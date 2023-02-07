import os
from urllib.request import Request, urlopen
import xbmc
import xbmcgui
import time

USER_AGENT = ('Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36'
                           ' (KHTML, like Gecko) Chrome/35.0.1916.153 Safari'
                           '/537.36 SE 2.X MetaSr 1.0')

class Downloader:
    def __init__(self, url):
        self.url = url
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36'
        self.headers = {"User-Agent":self.user_agent, "Connection":'keep-alive', 'Accept':'audio/webm,audio/ogg,udio/wav,audio/*;q=0.9,application/ogg;q=0.7,video/*;q=0.6,*/*;q=0.5'}
        
    def get_urllib(self, decoding=True):
        req = Request(self.url, headers = self.headers)
        if decoding:
            return urlopen(req).read().decode('utf-8')
        else:
            return urlopen(req)
    
    def get_session(self, decoding=True, stream=False):
        import requests
        session = requests.Session()
        if decoding:
            return session.get(self.url,headers=self.headers, stream=stream).content.decode('utf-8')
        else:
            return session.get(self.url,headers=self.headers, stream=stream)
    
    def get_requests(self, decoding=True, stream=False):
        import requests
        if decoding:
            return requests.get(self.url, headers=self.headers, stream=stream).content.decode('utf-8')
        else:
            return requests.get(self.url, headers=self.headers, stream=stream)
    
    def get_length(self, response, meth = 'session'):
        try:
            if meth in ['session', 'requests']:
                # return response.headers['X-Dropbox-Content-Length']
                return response.getheader('content-length')
            elif meth=='urllib':
                return response.getheader('content-length')
        except KeyError:
            return None

    def _is_url(url):
        try:  # Python 3
            from urllib.parse import urlparse
        except ImportError:  # Python 2
            from urlparse import urlparse

        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False

    def get_keyboard(default="", heading="", hidden=False):
        keyboard = xbmc.Keyboard(default, heading, hidden)
        keyboard.doModal()
        if keyboard.isConfirmed():
            return keyboard.getText()
        return default

    def _check_url(self, url, cred):
        import requests
        print('###url: ', url)
    # if self._is_url(url):
        try:
            response = requests.head(url, headers={'user-agent': USER_AGENT}, allow_redirects=True, auth=cred)
            
            if response.status_code < 300:
                # logging.log("URL check passed for {0}: Status code [{1}]".format(url, response.status_code), level=xbmc.LOGDEBUG)
                return True
            elif response.status_code < 400:
                # logging.log("URL check redirected from {0} to {1}: Status code [{2}]".format(url, response.headers['Location'], response.status_code), level=xbmc.LOGDEBUG)
                return self._check_url(response.headers['Location'])
            elif response.status_code == 401:
                # logging.log("URL requires authentication for {0}: Status code [{1}]".format(url, response.status_code), level=xbmc.LOGDEBUG)
                return 'auth'
            else:
                # logging.log("URL check failed for {0}: Status code [{1}]".format(url, response.status_code), level=xbmc.LOGDEBUG)
                return False
        except Exception as e:
            # logging.log("URL check error for {0}: [{1}]".format(url, e), level=xbmc.LOGDEBUG)
            return False
        # else:
            # logging.log("URL is not of a valid schema: {0}".format(url), level=xbmc.LOGDEBUG)
            # return False

    def open_url(self, url, stream=False, check=False, cred=None, count=0):
        import requests
        if not url:
            return False

        
        dialog = xbmcgui.Dialog()
        user_agent = {'user-agent': USER_AGENT}
        count = 0
        

        valid = self._check_url(url, cred)

        if not valid:
            return False
        else:
            if check:
                return True if valid else False
                
            if valid == 'auth' and not cred:
                cred = (self.get_keyboard(heading='Username'), self.get_keyboard(heading='Password'))
                
            response = requests.get(url, headers=user_agent, timeout=10.000, stream=stream, auth=cred)

            if response.status_code == 401:
                retry = dialog.yesno('CONFIG.ADDONTITLE', 'Either the username or password were invalid. Would you like to try again?', yeslabel='Try Again', nolabel='Cancel')
                
                if retry and count < 3:
                    count += 1
                    cred = (self.get_keyboard(heading='Username'), self.get_keyboard(heading='Password'))
                    
                    response = open_url(url, stream, check, cred, count)
                else:
                    dialog.ok(CONFIG.ADDONTITLE, 'Authentication Failed.')
                    return False
            
            return response
    
    def download_build(self, name,zippath,meth='session', stream=True):

        dp = xbmcgui.DialogProgress()
        dp.create(name, 'Downloading your build...')
        dp.update(0, 'Downloading your build...')
        cancelled = False
        tempzip = open(zippath, 'wb')

        response = self.open_url(self.url, stream)

        if not response:
            # logging.log_notify(CONFIG.ADDONTITLE,
                            #    '[COLOR {0}]Build Install: Invalid Zip Url![/COLOR]'.format(CONFIG.COLOR2))
            return
        else:
            total = response.headers.get('content-length')

        if total is None:
            tempzip.write(response.content)
        else:
            downloaded = 0
            total = int(total)
            start_time = time.time()
            mb = 1024*1024
            
            for chunk in response.iter_content(chunk_size=max(int(total/512), mb)):
                downloaded += len(chunk)
                tempzip.write(chunk)
                
                done = int(100 * downloaded / total)
                kbps_speed = downloaded / (time.time() - start_time)
                
                if kbps_speed > 0 and not done >= 100:
                    eta = (total - downloaded) / kbps_speed
                else:
                    eta = 0
                
                kbps_speed = kbps_speed / 1024
                type_speed = 'KB'
                
                if kbps_speed >= 1024:
                    kbps_speed = kbps_speed / 1024
                    type_speed = 'MB'
                    
                currently_downloaded = '[COLOR %s][B]Size:[/B] [COLOR %s]%.02f[/COLOR] MB of [COLOR %s]%.02f[/COLOR] MB[/COLOR]' % ('yellow', 'cyan', downloaded / mb, 'cyan', total / mb)
                speed = '[COLOR %s][B]Speed:[/B] [COLOR %s]%.02f [/COLOR]%s/s ' % ('yellow', 'cyan', kbps_speed, type_speed)
                div = divmod(eta, 60)
                speed += '[B]ETA:[/B] [COLOR %s]%02d:%02d[/COLOR][/COLOR]' % ('cyan', div[0], div[1])
                
                dp.update(done, '\n' + str(currently_downloaded) + '\n' + str(speed)) 
                if dp.iscanceled():
                    cancelled = True
                    break

        if cancelled:
            xbmc.sleep(1000)
            os.unlink(zippath)
            dialog = xbmcgui.Dialog()
            dialog.ok('Cancelled', 'Download Cancelled')
            return
            
        tempzip.close()

    
    def download_zip(self, dest):
        r = self.get_requests(decoding=False, stream=True)
        with open(dest, "wb") as f:
              for ch in r.iter_content(chunk_size = 2391975):
                  if ch:
                      f.write(ch)
                  f.close()