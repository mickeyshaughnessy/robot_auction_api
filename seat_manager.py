import json, time

class SeatManager:
    def __init__(self):
        self.seats = {}
        try:
            with open('seats.dat', 'r') as f:
                for line in f:
                    seat = json.loads(line)
                    self.seats[seat['id']] = seat
        except FileNotFoundError:
            print('No seats file found. Run generate_seats.py first')
            
    def assign_seat(self, seat_id, owner):
        if seat_id not in self.seats:
            return False, 'Seat does not exist'
        if self.seats[seat_id]['owner']:
            return False, 'Seat already owned'
            
        self.seats[seat_id]['owner'] = owner
        self.seats[seat_id]['assigned'] = int(time.time())
        self._save()
        return True, 'Seat assigned successfully'
        
    def transfer_seat(self, seat_id, old_owner, new_owner):
        if seat_id not in self.seats:
            return False, 'Seat does not exist'
        if self.seats[seat_id]['owner'] != old_owner:
            return False, 'Not authorized to transfer this seat'
            
        self.seats[seat_id]['owner'] = new_owner
        self.seats[seat_id]['transferred'] = int(time.time())
        self._save()
        return True, 'Seat transferred successfully'
        
    def get_owner_seats(self, owner):
        return {id: data for id, data in self.seats.items() 
                if data['owner'] == owner}
                
    def verify_phrase(self, seat_id, phrase):
        if seat_id not in self.seats:
            return False
        return self.seats[seat_id]['phrase'] == phrase
        
    def _save(self):
        with open('seats.dat', 'w') as f:
            for seat in self.seats.values():
                f.write(f'{json.dumps(seat)}\n')

if __name__ == '__main__':
    print('Loading seat data...')
    sm = SeatManager()
    print('Seat data loaded')
    
    print('\nAssigning seats to @satori_jojo...')
    for i in range(110):
        if i % 10 == 0:
            print(f'Processing seat {i}')
        sm.assign_seat(f'RSX{i:07d}', '@satori_jojo')
    print(f"@satori_jojo now owns {len(sm.get_owner_seats('@satori_jojo'))} seats")
    
    print('\nAssigning seats to @aftabahmed_dr...')
    for i in range(110, 1110):
        if i % 100 == 0:
            print(f'Processing seat {i}')
        sm.assign_seat(f'RSX{i:07d}', '@aftabahmed_dr')
    print(f"@aftabahmed_dr now owns {len(sm.get_owner_seats('@aftabahmed_dr'))} seats")
    
    print('\nAssigning seats to @AJAmmirabilis...')
    for i in range(1110, 11110):
        if i % 1000 == 0:
            print(f'Processing seat {i}')
        sm.assign_seat(f'RSX{i:07d}', '@AJAmmirabilis')
    print(f"@AJAmmirabilis now owns {len(sm.get_owner_seats('@AJAmmirabilis'))} seats")
    
    print('\nAll assignments complete!')