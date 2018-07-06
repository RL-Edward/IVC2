from cloudquant.interfaces import Strategy
from collections import OrderedDict

class IVC2(Strategy):
    @classmethod
    def is_symbol_qualified(cls, symbol, md, service, account):
        return symbol == "MSFT"
    
    def on_start(self, md, order, service, account):
        self.currentDay = self.Day()
        self.news_count = 0
        
    def on_finish(self, md, order, service, account):
        print "Symbol: " + self.symbol
        print "# prints each minute: " + str(self.currentDay.get_day_average_prints())
        print "# prints at 11:00: " + str(self.currentDay.ts_to_minutes["11:00"].print_count)
        print "Ave Range of minute bars: " + str(self.currentDay.get_day_average_range())
        print "Ave Volume of minute bars: " + str(self.currentDay.get_day_volume_average())
        print "# prints above ask at 11:00: " + str(self.currentDay.ts_to_minutes["11:00"].prints_above_ask)
        print "# prints below bid at 11:00: " + str(self.currentDay.ts_to_minutes["11:00"].prints_below_bid)
        print "Ratio of Vol(@|>ask)/Vol(@|<bid) at 11:00: " + str(self.currentDay.get_ratio_exec_ask_bid("11:00"))
        print "# of B. ask inc and dec at 11:00: " + str(self.currentDay.get_BA_count_increase("11:00")) + str(self.currentDay.get_BA_count_decrease("11:00"))
        print "# of B. bid inc and dec at 11:00: " + str(self.currentDay.get_BB_count_increase("11:00")) + str(self.currentDay.get_BB_count_decrease("11:00"))
        print ""
        print "# of prints in day: " + str(self.currentDay.get_day_count_print())
        #print "Print count for each minute: " + str(self.currentDay.get_print_count_for_each_min())
        print "All prints for 11:00: " + str(self.currentDay.ts_to_minutes["11:00"].last_price)
        #print "All ranges for each minute: " + str(tuple(self.currentDay.ts_to_minutes[ts].get_range() for ts in self.currentDay.ts_to_minutes))
        print "# of news: " + str(self.news_count)
        
    def on_trade(self, event, md, order, service, account):
        ts = str(service.time_to_string(event.timestamp)[11:16])

        if self.currentDay.exists(ts):
            self.currentDay.add_last(ts, event.last, event.last_size, event.ask, event.bid)
        else:   
            self.currentDay.add_new_minute(ts)
            self.currentDay.add_last(ts, event.last, event.last_size, event.ask, event.bid)
                
    def on_news(self, event, md, order, service, account):
        self.news_count += 1
    
    class Day:
        def __init__(self):
            self.ts_to_minutes = OrderedDict()
            self.size_ts_to_minutes = 0
            self.previous_ask = None
            self.previous_bid = None
            
        #Returns true if the minute exists within the day
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
            
        def to_string(self):
            for ts in self.ts_to_minutes:
                print ts + " " + str(self.ts_to_minutes[ts].get_count()) + " " + self.ts_to_minutes[ts].to_string() 
        
        def get_ratio_exec_ask_bid(self, ts):
            return float(self.get_vol_exec_ator_above_ask(ts))/float(self.get_vol_exec_ator_below_bid(ts))
                
        def get_BA_count_increase(self, ts):
            return self.ts_to_minutes[ts].BA_increase_count
        
        def get_BA_count_decrease(self, ts):
            return self.ts_to_minutes[ts].BA_decrease_count    
        
        def get_BB_count_increase(self, ts):
            return self.ts_to_minutes[ts].BB_increase_count
        
        def get_BB_count_decrease(self, ts):
            return self.ts_to_minutes[ts].BB_decrease_count
        
        def get_day_count_print(self):
            return sum(tuple(self.ts_to_minutes[ts].print_count for ts in self.ts_to_minutes)) 
        
        def get_print_count_for_each_min(self):
            return tuple(self.ts_to_minutes[ts].print_count for ts in self.ts_to_minutes)
        
        def get_day_sum_range(self):
            return sum(tuple(self.ts_to_minutes[ts].get_range() for ts in self.ts_to_minutes))
        
        def get_day_sum_volume(self):
            return sum(tuple(self.ts_to_minutes[ts].get_total_volume() for ts in self.ts_to_minutes))
        
        def get_day_average_prints(self):
            return float(self.get_day_count_print())/float(self.size_ts_to_minutes)
        
        def get_day_average_range(self):
            return float(self.get_day_sum_range())/float(self.size_ts_to_minutes)
        
        def get_day_volume_average(self):
            return float(self.get_day_sum_volume())/float(self.size_ts_to_minutes)
        
        def get_count_prints_above_ask(self):
            return tuple(self.ts_to_minutes[ts].get_count_prints_above_ask() for ts in self.ts_to_minutes)
        
        def get_count_prints_below_bid(self):
            return tuple(self.ts_to_minutes[ts].get_count_prints_below_bid() for ts in self.ts_to_minutes)
        
        def get_vol_exec_ator_above_ask(self, ts):
            return self.ts_to_minutes[ts].vol_at_or_above_ask
            
        def get_vol_exec_ator_below_bid(self, ts):
            return self.ts_to_minutes[ts].vol_at_or_below_bid 
    
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
            
            def get_total_volume(self):
                return self.total_size
                
            def get_count(self):
                return self.print_count

            def get_timestamp(self):
                return self.timestamp
            
            def get_prints(self):
                return ' '.join(str(last)for last in self.last_price)
                
            def set_high(self, last):
                self.high = last if (last > self.high) else self.high
            
            def set_low(self, last):
                self.low = last if (last < self.low or self.low == None) else self.low
            
            def get_range(self):
                return abs(self.high - self.low)

            def get_extrema(self):
                return str(self.high) + " " + str(self.low)
            
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
            
            def get_count_prints_above_ask(self):
                return self.prints_above_ask
            
            def get_count_prints_below_bid(self):
                return self.prints_below_bid
            
            def to_string(self):
                return str(self.get_timestamp()) + str(self.get_count()) + str(self.get_prints()) 
            
            def print_high_low(self):
                return "Timestamp: " + self.timestamp + " Extrema: " + self.get_extrema()
            
            