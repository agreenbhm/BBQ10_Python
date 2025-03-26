import board
import digitalio
import storage

# Setup the row/col pins for the spacebar key
# 'spac' is at ROW6/COL1 → row_idx=5, col_idx=0
row = digitalio.DigitalInOut(board.GP5)   # ROW6
col = digitalio.DigitalInOut(board.GP9)   # COL1

# Tri-state everything first
row.switch_to_input(pull=None)
col.switch_to_input(pull=None)

# Drive COL1 low, read ROW6
col.switch_to_output(value=False)
row.switch_to_input(pull=digitalio.Pull.UP)
held = not row.value  # False = pulled low by keypress

# Cleanup
col.deinit()
row.deinit()

# Disable storage unless spacebar held
if not held:
    storage.disable_usb_drive()
