from cloudquant.interfaces import Strategy
from collections import OrderedDict

class IVC2(Strategy):
    
    #############################################################################
    #IVC2 or Intraday Variable Calculator 2 serves to collect current day trading data as it occurs and subsequently perform calculations on said data.
    #Note: This script does not enter any positions.
    #Goal:
    #1. Average numer of prints each minute during market hours.
    #2. Numer of prints for this minute during market hours.
    #3. Average range of minute bar (do not use bar data) use high - low.
    #4. Average volume of minute bar (do not use bar data) during market hours.
    #5. Number of prints above the ask this minute.
    #6. Number of prints below the bid this minue.
    #7. Volume done at or above the current ask this minute / Volume at or below the current bid this minute.
    #8. Number of best ask price increases and decreases this minute.
    #9. Number of best bid price increases and decreases this minute.
    #10.Number of news events today. (pre and post market)
    #   
    #Control flow:
    #This program contains 2 extra classes call Day and MinuteBar;
    #Day aptly stores all the minute bars that are formed throughout the day.  
    #   They may be found in the dictionary: ts_to_minutes
    #   ts_to_minutes is not a dictionary of dictionaries, rather it is a dictionary of objects or MinuteBars which contain relevant data regarding a minute.
    #   Objects or instances of MinuteBars are created as new minutes are encoutered through on_trade
    #   To access the recordings at 1:30 PM ET you would use ts_to_minutes[13:30] followed by .last_price, .last_size, etc.
    #   The last or prints for a minute are stored as a list in MinuteBar, they are stored as they appear as such the most recent print in a MinuteBar may be found as
    #       ts_to_minutes[13:30].last_price[-1]
    #   The functions needed required to retreieve the intrada values can be found below the utility function section within the Day class.
    #############################################################################
    
    @classmethod
    def is_symbol_qualified(cls, symbol, md, service, account):
        return symbol == "MSFT"
    
    def on_start(self, md, order, service, account):
        self.currentDay = self.Day()
        self.news_count = 0
        
    def on_finish(self, md, order, service, account):
        print "Symbol: " + self.symbol
        
        #1. Average numer of prints each minute during market hours.
        print "Average number of prints each minute: " + str(self.currentDay.get_day_average_prints())
        
        #2. Numer of prints for this minute during market hours.
        print "Number prints at 11:00: " + str(self.currentDay.ts_to_minutes["11:00"].print_count)
        
        #3. Average range of minute bar (do not use bar data) use high - low.
        print "Average Range of minute bars for day: " + str(self.currentDay.get_day_average_range())
        
        #4. Average volume of minute bar (do not use bar data) during market hours.
        print "Average Volume of minute bars for day: " + str(self.currentDay.get_day_volume_average())
        
        #5. Number of prints above the ask this minute.
        print "Number of prints above ask at 11:00: " + str(self.currentDay.ts_to_minutes["11:00"].prints_above_ask)
        
        #6. Number of prints below the bid this minue.
        print "Number of prints below bid at 11:00: " + str(self.currentDay.ts_to_minutes["11:00"].prints_below_bid)
        
        #7. Volume done at or above the current ask this minute / Volume at or below the current bid this minute.
        print "Ratio of Vol(@|>ask)/Vol(@|<bid) at 11:00: " + str(self.currentDay.get_ratio_exec_ask_bid("11:00"))
        
        #8. Number of best ask price increases and decreases this minute.
        print "# of B. ask inc and dec at 11:00: " + str(self.currentDay.get_BA_count_increase("11:00")) + " " + str(self.currentDay.get_BA_count_decrease("11:00"))
        
        #9. Number of best bid price increases and decreases this minute.
        print "# of B. bid inc and dec at 11:00: " + str(self.currentDay.get_BB_count_increase("11:00")) + " " + str(self.currentDay.get_BB_count_decrease("11:00"))
        
        #10.Number of news events today. (pre and post market)
        print "Number of news events: " + str(self.news_count)
        
    def on_trade(self, event, md, order, service, account):
        if event.timestamp >= service.time(9,30) and event.timestamp < md.market_close_time - service.time_interval(0,5,0,0):
            ts = str(service.time_to_string(event.timestamp)[11:16])
            if self.currentDay.exists(ts):
                self.currentDay.add_last(ts, event.last, event.last_size, event.ask, event.bid)
            else:   
                self.currentDay.add_new_minute(ts)
                self.currentDay.add_last(ts, event.last, event.last_size, event.ask, event.bid)
                
    def on_news(self, event, md, order, service, account):
        self.news_count += 1
    
    #Day stores all the minutes for the trading day and then proceeds to calculate the neccessary intraday variables requested.
    class Day:
        def __init__(self):
            self.ts_to_minutes = OrderedDict()
            self.size_ts_to_minutes = 0
            self.previous_ask = None
            self.previous_bid = None
    
        #########################################################################
        #Core Methods. (Meant to be called upon from outside the class instance)
        #########################################################################
        
        #1. Average numer of prints each minute during market hours.
        def get_day_average_prints(self):
            return float(self.get_day_count_print())/float(self.size_ts_to_minutes)
         
        #2. Numer of prints for this minute during market hours.
        #   Can be found any minute by using ts_to_minutes["11:00"].print_count
        
        #3. Average range of minute bar (do not use bar data) use high - low.
        def get_day_average_range(self):
            return float(self.get_day_sum_range())/float(self.size_ts_to_minutes)
        
        #4. Average volume of minute bar (do not use bar data) during market hours.     
        def get_day_volume_average(self):
            return float(self.get_day_sum_volume())/float(self.size_ts_to_minutes)    
        
        #5. Number of prints above the ask this minute.
            #Can be found for any minute by using ts_to_minutes["11:00"].prints_above_ask
        
        #6. Number of prints below the bid this minute.
            #Can be found for any minute by using ts_to_minutes["11:00"].prints_below_bid
        
        #7. Volume done at or above the current ask this minute / Volume at or below the current bid this minute.
            #ts refers to timestamp, give it a minute "11:00" and it will return a calculated value for that minute.
        def get_ratio_exec_ask_bid(self, ts):
            return float(self.get_vol_exec_ator_above_ask(ts))/float(self.get_vol_exec_ator_below_bid(ts))
        
        #8. Number of best ask price increases and decreases this minute.
            #ts refers to timestamp, give it a minute "11:00" and it will return a calculated value for that minute.
        def get_BA_count_increase(self, ts):
            return self.ts_to_minutes[ts].BA_increase_count
        
        def get_BA_count_decrease(self, ts):
            return self.ts_to_minutes[ts].BA_decrease_count    
        
        #9. Number of best bid price increases and decreases this minute.
            #ts refers to timestamp, give it a minute "11:00" and it will return a calculated value for that minute.
        def get_BB_count_increase(self, ts):
            return self.ts_to_minutes[ts].BB_increase_count
        
        def get_BB_count_decrease(self, ts):
            return self.ts_to_minutes[ts].BB_decrease_count
        
        #10.Number of news events today. (pre and post market)
        #News events are tallied outside of this class. To retrieve the tally call self.news_count on on_finish
        
        #########################################################################
        #Utility Methods. (Not meant to be called outside of the class instance.)
        #########################################################################
        
        def exists(self, ts): 
            return True if ts in self.ts_to_minutes else False
        
        def add_new_minute(self, ts):
            self.ts_to_minutes[ts] = self.MinuteBar(ts)
            self.size_ts_to_minutes += 1
            
        def add_last(self, ts, last, last_size, ask, bid):
            self.previous_ask = ask if self.previous_ask == None else self.previous_ask
            self.previous_bid = bid if self.previous_bid == None else self.previous_bid
            self.ts_to_minutes[ts].add_last(last, last_size, ask, bid, self.previous_ask, self.previous_bid)
            self.previous_ask = ask
            self.previous_bid = bid
            
        def get_day_count_print(self):
            return sum(tuple(self.ts_to_minutes[ts].print_count for ts in self.ts_to_minutes)) 
        
        def get_print_count_for_each_min(self):
            return tuple(self.ts_to_minutes[ts].print_count for ts in self.ts_to_minutes)
        
        def get_day_sum_range(self):
            return sum(tuple(self.ts_to_minutes[ts].get_range() for ts in self.ts_to_minutes))
        
        def get_day_sum_volume(self):
            return sum(tuple(self.ts_to_minutes[ts].total_size for ts in self.ts_to_minutes))
    
        def get_count_prints_above_ask(self):
            return tuple(self.ts_to_minutes[ts].prints_above_ask for ts in self.ts_to_minutes)
        
        def get_count_prints_below_bid(self):
            return tuple(self.ts_to_minutes[ts].prints_below_bid for ts in self.ts_to_minutes)
        
        def get_vol_exec_ator_above_ask(self, ts):
            return self.ts_to_minutes[ts].vol_at_or_above_ask
            
        def get_vol_exec_ator_below_bid(self, ts):
            return self.ts_to_minutes[ts].vol_at_or_below_bid 
               
    
        #MinuteBar is a storage container that stores all the relevant information we wish to capture during a trading day.
        #   The functions located within are utility function and are soley meant to automate certain calculations.
        class MinuteBar:
            def __init__(self, ts):
                self.last_price = []
                self.last_size = []
                self.ask = []
                self.bid = []
                self.print_count =  0
                self.total_size = 0
                self.timestamp = ts
                self.high = None
                self.low = None
                self.prints_above_ask = 0
                self.prints_below_bid = 0
                self.vol_at_or_above_ask = 0
                self.vol_at_or_below_bid = 0
                self.BA_increase_count = 0
                self.BA_decrease_count = 0
                self.BB_increase_count = 0
                self.BB_decrease_count = 0
                
            def add_last(self, last, last_size, ask, bid, previous_ask, previous_bid):
                self.last_price.append(last)
                self.last_size.append(last_size)
                self.add_volume(last_size)
                self.print_count += 1
                self.set_high(last)
                self.set_low(last)
                self.is_print_above_ask(last, ask)
                self.is_print_below_bid(last, bid)
                self.vol_exec_ator_above_ask(last, last_size, ask)
                self.vol_exec_ator_below_bid(last, last_size, bid)
                self.BA_change(ask, previous_ask)
                self.BB_change(bid, previous_bid)
                self.ask.append(ask)
                self.bid.append(bid)
                
            def add_volume(self, last_size):
                self.total_size += last_size

            def set_high(self, last):
                self.high = last if (last > self.high) else self.high
            
            def set_low(self, last):
                self.low = last if (last < self.low or self.low == None) else self.low
            
            def get_range(self):
                return abs(self.high - self.low)
            
            def is_print_above_ask(self, last, ask):
                if last > ask:
                    self.prints_above_ask += 1
            
            def is_print_below_bid(self, last, bid):
                if last < bid:
                    self.prints_below_bid += 1
            
            def vol_exec_ator_above_ask(self, last, last_size, ask):
                if last >= ask:
                    self.vol_at_or_above_ask += last_size
                
            def vol_exec_ator_below_bid(self, last, last_size, bid):
                if last <= bid:
                    self.vol_at_or_below_bid += last_size
                    
            def BA_change(self, ask, previous_ask):
                if ask > previous_ask:
                    self.BA_increase_count += 1
                elif ask < previous_ask:
                    self.BA_decrease_count += 1
                
            def BB_change(self, bid, previous_bid):
                if bid > previous_bid:
                    self.BB_increase_count += 1
                elif bid < previous_bid:
                    self.BB_decrease_count += 1
            
            