<?php
namespace ALT\Core;
use alteredbranchd;

/*
 * Game: a wrapper over table object to allow more generic modules
 */
class Game
{
  public static function get()
  {
    return alteredbranchd::get();
  }
}
